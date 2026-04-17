import sqlite3

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from typing_extensions import TypedDict
from langgraph.graph.state import StateGraph, START

from agent.time_travel.TimeTravelDemo04 import history


# Define subgraph
class Other_SubgraphState(TypedDict):
    # note that none of these keys are shared with the parent graph state
    bar: str
    baz: str

def other_subgraph_node_1(state: Other_SubgraphState):
    return {"baz": "baz"}

def other_subgraph_node_2(state: Other_SubgraphState):
    return {"bar": state["bar"] + state["baz"]}

other_subgraph_builder = StateGraph(Other_SubgraphState)
other_subgraph_builder.add_node(other_subgraph_node_1)
other_subgraph_builder.add_node(other_subgraph_node_2)
other_subgraph_builder.add_edge(START, "other_subgraph_node_1")
other_subgraph_builder.add_edge("other_subgraph_node_1", "other_subgraph_node_2")

checkpointer1 =  SqliteSaver(sqlite3.connect("checkpoint.db",check_same_thread=False))
other_subgraph = other_subgraph_builder.compile(checkpointer=checkpointer1)





class SubgraphState(TypedDict):
    # note that none of these keys are shared with the parent graph state
    bar: str
    baz: str

def subgraph_node_1(state: SubgraphState):
    return {"baz": "baz"}

def subgraph_node_2(state: SubgraphState):
    return {"bar": state["bar"] + state["baz"]}

subgraph_builder = StateGraph(SubgraphState)
subgraph_builder.add_node(subgraph_node_1)
subgraph_builder.add_node(subgraph_node_2)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph_builder.add_edge("subgraph_node_1", "subgraph_node_2")

#subgraph = subgraph_builder.compile()
# () {'node_1': {'foo': 'hi! foo'}}
# ('node_2:90ee24d9-1861-eae8-b4cc-31e363605831',) {'subgraph_node_1': {'baz': 'baz'}}
# ('node_2:90ee24d9-1861-eae8-b4cc-31e363605831',) {'subgraph_node_2': {'bar': 'hi! foobaz'}}
# () {'node_2': {'foo': 'hi! foobaz'}}

#subgraph = subgraph_builder.compile(checkpointer=True)
# () {'node_1': {'foo': 'hi! foo'}}
# ('node_2',) {'subgraph_node_1': {'baz': 'baz'}}
# ('node_2',) {'subgraph_node_2': {'bar': 'hi! foobaz'}}
# () {'node_2': {'foo': 'hi! foobaz'}}

#subgraph = subgraph_builder.compile(checkpointer=None)
# () {'node_1': {'foo': 'hi! foo'}}
# ('node_2',) {'subgraph_node_1': {'baz': 'baz'}}
# ('node_2',) {'subgraph_node_2': {'bar': 'hi! foobaz'}}
# () {'node_2': {'foo': 'hi! foobaz'}}
checkpointer =  SqliteSaver(sqlite3.connect("checkpoint.db",check_same_thread=False))
subgraph = subgraph_builder.compile(checkpointer=checkpointer)



# Define parent graph
class ParentState(TypedDict):
    foo: str

def node_1(state: ParentState):
    return {"foo": "hi! " + state["foo"]}

def node_2(state: ParentState):
    # Transform the state to the subgraph state
    config1={"configurable": {"thread_id": "134"}}
    config2 = {"configurable": {"thread_id": "135"}}
    response = subgraph.invoke({"bar": state["foo"]},config=config1)
    response2 = other_subgraph.invoke({"bar": state["foo"]},config=config2)
    # Transform response back to the parent state
    return {"foo": response["bar"]+response2["bar"]}


builder = StateGraph(ParentState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "133"}}
for chunk in graph.stream({"foo": "foo"},config=config,subgraphs=True, version="v2"):
    if chunk["type"] == "updates":
        print(chunk["ns"], chunk["data"])

