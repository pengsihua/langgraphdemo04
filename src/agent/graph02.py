from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START
from langgraph.graph import StateGraph

class State(TypedDict, total=False):
    txt: str



def node_a(state: State) -> dict:
    return {"txt": state["txt"] + "a"}


def node_b(state: State) -> dict:
    checkpoint_ns = config["configurable"].get("checkpoint_ns","sdffsd")
    print(checkpoint_ns)
    return {"txt": state["txt"] + "b"}


graph = StateGraph(State)
graph.add_node("node_a", node_a)
graph.add_node("node_b", node_b)
graph.add_edge(START, "node_a")
graph.add_edge("node_a", "node_b")

checkpointer = InMemorySaver()

cgraph = graph.compile(checkpointer=checkpointer)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}



res = cgraph.invoke({"txt":"sdfsdfds"},config=config)
print(res)

print("get_state",cgraph.get_state(config))

print(list(cgraph.get_state_history(config)))


history = list(cgraph.get_state_history(config))


# Find the checkpoint before a specific node executed
before_node_b = next(s for s in history if s.next == ("node_b",))
print(before_node_b)

# Find a checkpoint by step number
step_2 = next(s for s in history if s.metadata["step"] == 2)
print(step_2)

# Find checkpoints created by update_state
forks = [s for s in history if s.metadata["source"] == "update"]
print(forks)

# Find the checkpoint where an interrupt occurred
interrupted = next(
    s for s in history
    if s.tasks and any(t.interrupts for t in s.tasks)
)
print(interrupted)
