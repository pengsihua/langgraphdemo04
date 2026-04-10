from langchain.tools import tool
from langgraph.config import get_stream_writer
from typing import TypedDict

from langgraph.constants import START, END
from langgraph.graph import StateGraph


class State(TypedDict):
    topic: str
    joke: str


@tool
def query_database(query: str) -> str:
    """Query the database."""
    # Access the stream writer to send custom data
    writer = get_stream_writer()
    # Emit a custom key-value pair (e.g., progress update)
    writer({"data": "Retrieved 0/100 records", "type": "progress"})
    # perform query
    # Emit another custom key-value pair
    writer({"data": "Retrieved 100/100 records", "type": "progress"})
    return "some-answer"

def refine_topic(state: State):
    topic = state["topic"] + " and cats"
    some_answer =query_database.invoke("test")
    return {"topic": some_answer}


def generate_joke(state: State):
    joke = f"This is a joke about {state["topic"]}"
    return {"joke": joke}

graph = (
    StateGraph(State).add_node("refine_topic", refine_topic)
    .add_node("generate_joke", generate_joke)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_joke")
    .add_edge("generate_joke", END).compile())




# Set stream_mode="custom" to receive the custom data in the stream
for chunk in graph.stream({"topic": "ice cream"}, stream_mode=["custom","updates"], version="v2"):
    if chunk["type"] == "custom":
        print(f"{chunk['data']['type']}: {chunk['data']['data']}")

    if chunk["type"] == "updates":
        print(f"{chunk['data']}")