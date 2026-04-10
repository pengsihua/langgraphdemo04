import asyncio

from langchain.chat_models import init_chat_model
from typing import TypedDict
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from websockets.version import tag


class State(TypedDict):
    topic: str
    joke: str
    poem: str


model_1 = init_chat_model(model="glm-5",
                          model_provider="openai",
                          api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                          base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                          tags=["joke"]
                          )

model_2 = init_chat_model(model="glm-5",
                          model_provider="openai",
                          api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                          base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                          tags=["poem"]
                          )


async def call_model(state: State, config):
    print("state", state)
    print("config", config)
    topic = state["topic"]
    print("Writing joke...")

    joke_response = model_1.invoke(
        [
            {"role": "user", "content": f"Generate a joke about {state['topic']}"}
        ],
        config
    )
    # print("content", joke_response.content)
    poem_response = model_2.invoke(
        [
            {"role": "user", "content": f"Generate a poem about {state['topic']}"}
        ],
        config
    )

    # print("content", model_response.content)

    return {"joke": joke_response.content, "poem": poem_response.content}


graph = (
    StateGraph(State)
    .add_node(call_model)
    .add_edge(START, "call_model")
    .compile()
)


async def main():
    async  for chunk in graph.astream(
            {"topic": "cats"},
            stream_mode=["messages", "updates"],
            version="v2"
    ):
        if chunk['type'] == "messages":
            msg, metadata = chunk["data"]
            if metadata["tags"] == ["poem"]:
                print(msg.content, end="|", flush=True)

asyncio.run(main())