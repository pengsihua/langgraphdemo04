import asyncio
import operator
import json
from langgraph.config import get_stream_writer
from typing import TypedDict

from langgraph.func import task
from typing_extensions import Annotated
from langgraph.graph import StateGraph, START

from openai import AsyncOpenAI

openai_client = AsyncOpenAI(api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
model_name = "glm-5"



async def stream_tokens(model_name: str, messages: list[dict]):
    response = await openai_client.chat.completions.create(
        messages=messages, model=model_name, stream=True
    )
    role = None
    async for chunk in response:
        delta = chunk.choices[0].delta

        if delta.role is not None:
            role = delta.role

        if delta.content:
            yield {"role": role, "content": delta.content}


# this is our tool
@task
async def get_items(place: str) -> str:
    """Use this tool to list items one might find in a place you're asked about."""
    writer = get_stream_writer()
    response = ""
    async for msg_chunk in stream_tokens(
            model_name,
            [
                {
                    "role": "user",
                    "content": (
                            "Can you tell me what kind of items "
                            f"i might find in the following place: '{place}'. "
                            "List at least 3 such items separating them by a comma. "
                            "And include a brief description of each item."
                    ),
                }
            ],
    ):
        response += msg_chunk["content"]
        writer(msg_chunk)

    return response


class State(TypedDict):
    messages: Annotated[list[dict], operator.add]


# this is the tool-calling graph node
async def call_tool(state: State):
    ai_message = state["messages"][-1]
    tool_call = ai_message["tool_calls"][-1]

    function_name = tool_call["function"]["name"]
    if function_name != "get_items":
        raise ValueError(f"Tool {function_name} not supported")

    function_arguments = tool_call["function"]["arguments"]
    arguments = json.loads(function_arguments)

    function_response = await get_items(**arguments)
    tool_message = {
        "tool_call_id": tool_call["id"],
        "role": "tool",
        "name": function_name,
        "content": function_response,
    }
    return {"messages": [tool_message]}


graph = (
    StateGraph(State)
    .add_node(call_tool)
    .add_edge(START, "call_tool")
    .compile()
)

inputs = {
    "messages": [
        {
            "content": None,
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "1",
                    "function": {
                        "arguments": '{"place":"bedroom"}',
                        "name": "get_items",
                    },
                    "type": "function",
                }
            ],
        }
    ]
}


async def main():
    async for chunk in graph.astream(
            inputs,
            stream_mode="custom",
            version="v2",
    ):
        if chunk["type"] == "custom":
            print(chunk["data"]["content"], end="|", flush=True)
            print(chunk["data"]["content"], end="|", flush=True)


asyncio.run(main())
