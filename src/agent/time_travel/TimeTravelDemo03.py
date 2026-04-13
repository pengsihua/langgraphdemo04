from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command

class State(TypedDict):
    value: list[str]

def ask_human(state: State):
    answer = interrupt("What is your name?")
    return {"value": [f"Hello, {answer}!"]}

def final_step(state: State):
    return {"value": ["Done"]}

graph = (
    StateGraph(State)
    .add_node("ask_human", ask_human)
    .add_node("final_step", final_step)
    .add_edge(START, "ask_human")
    .add_edge("ask_human", "final_step")
    .compile(checkpointer=InMemorySaver())
)

config = {"configurable": {"thread_id": "1"}}

# First run: hits interrupt
graph.invoke({"value": []}, config,version='v2')
# Resume with answer
graph.invoke(Command(resume="Alice"), config,version='v2')

# Replay from before ask_human
history = list(graph.get_state_history(config))
for state in history:
    print(state)


before_ask = [s for s in history if s.next == ("ask_human",)][-1]

replay_result = graph.invoke(None, before_ask.config,version='v2')
print("replay_result:",replay_result)
# Pauses at interrupt — waiting for new Command(resume=...)

# Fork from before ask_human
fork_config = graph.update_state(before_ask.config, {"value": ["forked"]})
print("fork_config:",fork_config)
fork_result = graph.invoke(None, fork_config,version='v2')
# Pauses at interrupt — waiting for new Command(resume=...)
print("fork_result:",fork_result)

# Resume the forked interrupt with a different answer
res  = graph.invoke(Command(resume="Bob"), fork_config,version='v2')
# Result: {"value": ["forked", "Hello, Bob!", "Done"]}

print("res:",res)