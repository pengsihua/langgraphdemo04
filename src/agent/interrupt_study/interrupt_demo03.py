from typing import Annotated, TypedDict
import operator

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    vals: Annotated[list[str], operator.add]


def node_a(state):
    answer = interrupt("question_a")
    print(answer)
    return {"vals": [f"a:{answer}"]}


def node_b(state):
    answer = interrupt("question_b")
    print(answer)
    return {"vals": [f"b:{answer}"]}


graph = (
    StateGraph(State)
    .add_node("a", node_a)
    .add_node("b", node_b)
    .add_edge(START, "a")
    .add_edge(START, "b")
    .add_edge("a", END)
    .add_edge("b", END)
    .compile(checkpointer=InMemorySaver())
)

config = {"configurable": {"thread_id": "101"}}

# Step 1: invoke - both parallel nodes hit interrupt() and pause
interrupted_result = graph.invoke({"vals": []},config, version='v2')
print(interrupted_result)


# Step 2: resume all pending interrupts at once
resume_map = {
    i.id: f"answer for {i.value}"
    for i in interrupted_result.interrupts
}
print(resume_map)
result = graph.invoke(Command(resume=resume_map), config)

print("Final state:", result)
#> Final state: {'vals': ['a:answer for question_a', 'b:answer for question_b']}