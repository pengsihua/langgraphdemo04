from typing import TypedDict

from langgraph.config import get_stream_writer

from langgraph.graph import StateGraph
from langgraph.constants import START,END


class State(TypedDict, total=False):
    topic: str
    joke: str
    progress:str


def generate_joke(state: State):
    wirter = get_stream_writer()
    wirter({"status": "thinking of a joke...","progress":"50"})
    return {"joke": f"Why did the {state['topic']} go to school? To get a sundae education!"}


graph = (
    StateGraph(State)
    .add_node(generate_joke)
    .add_edge(START, "generate_joke")
    .add_edge("generate_joke", END)
    .compile()
)


for chunk in graph.stream(
        {"topic": "ice cream"},
        stream_mode=["updates", "custom"],
        version="v2"
):
    if chunk['type']=="updates":
        for node_name,state in chunk['data'].items():
            print(f"Node {node_name} updated: {state}")
    elif chunk["type"] == "custom":
        print(f"Status: {chunk['data']['status']}")

for chunk in graph.stream({"topic": "ice cream"}, stream_mode="updates", version="v2"):
    print(chunk["type"])  # "updates"
    print(chunk["ns"])    # ()
    print(chunk["data"])  # {"node_name": {"key": "value"}}


for chunk in graph.stream({"topic": "ice cream"}, stream_mode="updates"):
    print(chunk)  # {"node_name": {"key": "value"}}

print("\n\n\n\n\n")
for part in graph.stream(
    {"topic": "ice cream"},
    stream_mode=["values", "updates", "messages", "custom"],
    version="v2",
):
    if part["type"] == "values":
        # ValuesStreamPart — full state snapshot after each step
        print(f"State: topic={part['data']['topic']}")
    elif part["type"] == "updates":
        # UpdatesStreamPart — only the changed keys from each node
        for node_name, state in part["data"].items():
            print(f"Node `{node_name}` updated: {state}")
    elif part["type"] == "messages":
        # MessagesStreamPart — (message_chunk, metadata) from LLM calls
        msg, metadata = part["data"]
        print(msg.content, end="", flush=True)
    elif part["type"] == "custom":
        # CustomStreamPart — arbitrary data from get_stream_writer()
        print(f"Progress: {part['data']['progress']}%")