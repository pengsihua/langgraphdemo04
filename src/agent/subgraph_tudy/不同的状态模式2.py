import sqlite3

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from typing_extensions import TypedDict
from langgraph.graph.state import StateGraph, START


class SubgraphState(TypedDict):
    # note that none of these keys are shared with the parent graph state
    bar: str
    baz: str


def subgraph_node_1(state: SubgraphState):
    print("subgraph_node_1")
    return {"baz": "baz"}


def subgraph_node_2(state: SubgraphState):
    print("subgraph_node_2")
    return {"bar": state["bar"] + state["baz"]}


subgraph_builder = StateGraph(SubgraphState)
subgraph_builder.add_node(subgraph_node_1)
subgraph_builder.add_node(subgraph_node_2)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph_builder.add_edge("subgraph_node_1", "subgraph_node_2")

checkpointer = SqliteSaver(sqlite3.connect("checkpoint.db", check_same_thread=False))
subgraph = subgraph_builder.compile(checkpointer=True)


# Define parent graph
class ParentState(TypedDict):
    foo: str


def node_1(state: ParentState):
    print("node_1")
    return {"foo": "hi! " + state["foo"]}


def node_2(state: ParentState):
    print("node_2")
    # Transform the state to the subgraph state
    config1 = {"configurable": {"thread_id": "134"}}
    config2 = {"configurable": {"thread_id": "135"}}
    response = subgraph.invoke({"bar": state["foo"]})
    response2 = subgraph.invoke({"bar": state["foo"] + ",sdfsd"})
    # Transform response back to the parent state
    return {"foo": response["bar"] + response2["bar"]}


builder = StateGraph(ParentState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "133"}}
for chunk in graph.stream({"foo": "foo"}, config=config, subgraphs=True, version="v2"):
    if chunk["type"] == "updates":
        print(chunk["ns"], chunk["data"])

history = list(graph.get_state_history(config={"configurable": {"thread_id": "133"}}))

# before_joke = next(s for s in history if s.next == ("write_joke",))

for info in history:
    print(info)

sub_history = list(subgraph.get_state_history(config={"configurable": {"thread_id": "134"}}))
for info in sub_history:
    print("sub_history:", info)


fork_config = graph.update_state(
    sub_history[1].config,
    values={"foo": "chickens"},
)
response = graph.invoke(None, fork_config)

print("response:", response)
