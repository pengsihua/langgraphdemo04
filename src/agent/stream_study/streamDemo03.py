from typing import TypedDict

from langgraph.constants import START, END
from langgraph.graph import StateGraph


class State(TypedDict):
    topic: str
    joke: str


def refine_topic(state: State):
    topic = state["topic"] + " and cats"
    return {"topic": topic}


def generate_joke(state: State):
    joke = f"This is a joke about {state["topic"]}"
    return {"joke": joke}


graph = (
    StateGraph(State).add_node("refine_topic", refine_topic)
    .add_node("generate_joke", generate_joke)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_joke")
    .add_edge("generate_joke", END).compile())

for chunk in graph.stream(
        {"topic": "ice cream"},
        stream_mode=["updates", "values","tasks"],
        version="v2"
):
    # if chunk["type"] == "updates":
    #    print(chunk["data"])

    # print("\n\n\n\n\n")

    # if chunk["type"] == "values":
    #     print(chunk)

    if chunk['type'] == "tasks":
        print("tasks:",chunk["data"])