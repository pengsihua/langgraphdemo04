from typing import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph

checkpointer = MemorySaver()


class SubgraphState(TypedDict):
    foo: str  # 与父图共享
    bar: str


def subgraph_node_1(state: SubgraphState):
    return {"bar": "bar"}


def subgraph_node_2(state: SubgraphState):
    return {"foo": state["foo"] + state["bar"]}


subgraph_builder = StateGraph(SubgraphState)
subgraph_builder.add_node("subgraph_node_1", subgraph_node_1)
subgraph_builder.add_node("subgraph_node_2", subgraph_node_2)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph_builder.add_edge("subgraph_node_1", "subgraph_node_2")
subgraph = subgraph_builder.compile(checkpointer=checkpointer)


class ParentState(TypedDict):
    foo: str


def node_1(state: ParentState):
    return {"foo": "hi" + state["foo"]}


builder = StateGraph(ParentState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", subgraph)

builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")

graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "1"}}

for chunk in graph.stream(
        {"foo": "foo"},
        stream_mode=["updates", "values","checkpoints"],
        config=config,
        subgraphs=True,
        version="v2"
):
    if chunk["type"] == "updates":
        if chunk["ns"]:
            print(f"Subgraph: {chunk['ns']}:{chunk['data']}")
        else:
            print(f"Root: {chunk['data']}")

    # if chunk["type"] == "values":
    #     print(chunk)
    if chunk["type"] == "checkpoints":
        print("check:",chunk['data'])