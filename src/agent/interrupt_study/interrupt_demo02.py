import asyncio
import sqlite3
import uuid
from typing import TypedDict

from langchain_core.messages import AIMessageChunk
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command


class State(TypedDict, total=False):
    approved: bool
    name: str


def approval_node(state: State):
    # Pause and ask for approval
    approved = interrupt("Do you approve this action?")

    # When you resume, Command(resume=...) returns that value here
    print("approved:", approved)
    return {"approved": approved}


# checkpointer = SqliteSaver(sqlite3.connect("checkpoint.db", check_same_thread=False))
checkpointer = InMemorySaver()
builder = StateGraph(State)
builder.add_node("approval_node", approval_node)
builder.add_edge(START, "approval_node")
builder.add_edge("approval_node", END)
graph = builder.compile(checkpointer=checkpointer)

thread_id = "thread_id_0001"

config = {"configurable": {"thread_id": thread_id}}


# result = graph.invoke({"input": "data"}, config=config, version="v2")
# print(result)
# print("interrupts:", result.interrupts)


async def main():
    initial_input = {"xxxx": "xxxx"}
    while True:
        async for chunk in graph.astream(
                input=initial_input,
                stream_mode=["messages", "updates"],
                subgraphs=True,
                config=config,
                version="v2",
        ):
            if chunk["type"] == "messages":
                # Handle streaming message content
                msg, _ = chunk["data"]
                if isinstance(msg, AIMessageChunk) and msg.content:
                    print(msg.content)

            elif chunk["type"] == "updates":
                print("chunk:", chunk)
                # Check for interrupts in the updates data
                if "__interrupt__" in chunk["data"]:
                    interrupt_info = chunk["data"]["__interrupt__"][0].value
                    print(interrupt_info)
                    user_response = interrupt_info
                    initial_input = Command(resume=user_response)
                    print(initial_input)
                    break
                else:
                    current_node = list(chunk["data"].keys())[0]
        else:
            break


asyncio.run(main())
