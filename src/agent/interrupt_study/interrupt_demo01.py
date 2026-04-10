import sqlite3
import uuid
from typing import TypedDict

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
    return {"approved": approved}


checkpointer = SqliteSaver(sqlite3.connect("checkpoint.db", check_same_thread=False))

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

res = graph.invoke(Command(resume=False), config=config, version="v2")

print(res)
