from typing import Any, TypedDict
from langchain.chat_models import init_chat_model
from langgraph.graph import START, StateGraph

stream_model = init_chat_model(model="glm-5",
                               model_provider="openai",
                               api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                               base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                               tags=["joke"]
                               ).with_config(
    {"tags": ["nostream"]}
)
internal_model = init_chat_model(model="glm-5",
                                 model_provider="openai",
                                 api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                                 tags=["joke"]
                                 ).with_config(
    {"tags": ["nostream"]}
)


class State(TypedDict):
    topic: str
    answer: str
    notes: str


def answer(state: State) -> dict[str, Any]:
    r = stream_model.invoke(
        [{"role": "user", "content": f"Reply briefly about {state['topic']}"}]
    )
    return {"answer": r.content}


def internal_notes(state: State) -> dict[str, Any]:
    # Tokens from this model are omitted from stream_mode="messages" because of nostream
    r = internal_model.invoke(
        [{"role": "user", "content": f"Private notes on {state['topic']}"}]
    )
    return {"notes": r.content}


graph = (
    StateGraph(State)
    .add_node("write_answer", answer)
    .add_node("internal_notes", internal_notes)
    .add_edge(START, "write_answer")
    .add_edge("write_answer", "internal_notes")
    .compile()
)

initial_state: State = {"topic": "AI", "answer": "", "notes": ""}

for chunk in graph.stream(initial_state, stream_mode="messages",version="v2"):

    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        if msg.content:
            print(metadata["langgraph_node"])
