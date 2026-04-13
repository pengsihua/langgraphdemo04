
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver
from typing_extensions import TypedDict, NotRequired
from langchain_core.utils.uuid import uuid7

class State(TypedDict):
    topic: NotRequired[str]
    joke: NotRequired[str]


def generate_topic(state: State):
    return {"topic": "socks in the dryer"}


def write_joke(state: State):
    return {"joke": f"Why do {state['topic']} disappear? They elope!"}


checkpointer = InMemorySaver()
graph = (
    StateGraph(State)
    .add_node("generate_topic", generate_topic)
    .add_node("write_joke", write_joke)
    .add_edge(START, "generate_topic")
    .add_edge("generate_topic", "write_joke")
    .compile(checkpointer=checkpointer)
)

# Step 1: Run the graph
config = {"configurable": {"thread_id": str(uuid7())}}
#config = {"configurable": {"thread_id": "numm11"}}

result = graph.invoke({}, config)
#result = graph.invoke({}, config)
print("get_state",graph.get_state(config))

# Find checkpoint before write_joke
history = list(graph.get_state_history(config))
before_joke = next(s for s in history if s.next == ("write_joke",))

print("before_joke:",before_joke)
# Fork: update state to change the topic
fork_config = graph.update_state(
    before_joke.config,
    values={"topic": "chickens"},
    as_node="write_joke",
)
print("before_joke:",before_joke.config)
print("fork_config:",fork_config)

history1 = list(graph.get_state_history(config))
before_joke1 = next(s for s in history if s.next == ("write_joke",))
print("before_joke1:",before_joke1)

# Resume from the fork — write_joke re-executes with the new topic
fork_result = graph.invoke(None, fork_config)
print(fork_result)  # A joke about chickens, not socks


history2 = list(graph.get_state_history(config))
for state in history2:
    print(state)