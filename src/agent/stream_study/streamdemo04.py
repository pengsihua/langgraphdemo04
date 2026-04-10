from langchain.chat_models import init_chat_model
from typing import TypedDict
from langgraph.graph import StateGraph
from langgraph.constants import START, END


class State(TypedDict):
    topic: str
    joke: str = ""


model = init_chat_model(model="glm-5",
                        model_provider="openai",
                        api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                        )


def call_model(state: State):
    print(state)
    model_response = model.invoke(
        [
            {"role": "user", "content": f"Generate a joke about {state['topic']}"}
        ]
    )

    print("content",model_response.content)

    return {"joke": model_response.content}


graph = (
    StateGraph(State)
    .add_node(call_model)
    .add_edge(START, "call_model")
    .compile()
)

for chunk in graph.stream(
        {"topic": "ice cream"},
        stream_mode=["messages","updates","tasks"],
        version="v2"
):
    if chunk['type'] == "messages":
        message_chunk, metadata = chunk["data"]
        print(metadata)
        if message_chunk.content:
            print(message_chunk.content, end="|", flush=True)

    if chunk['type'] == "updates":
        print("update",chunk["data"], end="|", flush=True)

