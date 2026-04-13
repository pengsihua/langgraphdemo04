from operator import add
from typing import Annotated

from jedi.inference.gradual.typing import TypedDict
from langchain_core.utils.uuid import uuid7
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command


class State(TypedDict):
    value: Annotated[list[str], add]


def ask_name(state):
    name = interrupt("What is your name?")
    return {"value": [f"name:{name}"]}


def ask_age(state):
    age = interrupt("How old are you?")
    return {"value": [f"age:{age}"]}


# Graph: ask_name -> ask_age -> final
# After completing both interrupts:

buidler = StateGraph(State)

buidler.add_node("ask_name", ask_name)
buidler.add_node("ask_age", ask_age)
buidler.add_edge(START, "ask_name")
buidler.add_edge("ask_name", "ask_age")
buidler.add_edge("ask_age", END)

graph = buidler.compile(checkpointer=InMemorySaver())

config = {"configurable": {
    "thread_id": str(uuid7())
}}

result1 = graph.invoke({}, config, version='v2')

graph.invoke(Command(resume="pengsihua"), config, version='v2')

graph.invoke(Command(resume=12), config, version='v2')

# Fork from BETWEEN the two interrupts (after ask_name, before ask_age)
history = list(graph.get_state_history(config))
for ss in history:
    print(ss)

between = [s for s in history if s.next == ("ask_age",)][-1]

fork_config = graph.update_state(between.config, {"value": ["modified"]})
result = graph.invoke(None, fork_config,version='v2')
print(result)
ress = graph.invoke(Command(resume=22), config, version='v2')
print(ress)

# ask_name result preserved ("name:Alice")
# ask_age pauses at interrupt — waiting for new answer
