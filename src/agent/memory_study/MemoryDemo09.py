from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, MessagesState

model = init_chat_model(model="glm-5",
                        model_provider="openai",
                        api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                        )
summarization_model = model.bind(max_tokens=128)

def call_model(state: MessagesState):
    messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter="approximate",
        max_tokens=512,
        start_on="human",
        end_on=("human", "tool"),
    )
    print(messages)
    response = model.invoke(messages)
    return {"messages": [response]}

checkpointer = InMemorySaver()
builder = StateGraph(MessagesState)
builder.add_node(call_model)
builder.add_edge(START, "call_model")
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "1"}}
graph.invoke({"messages": "hi, my name is bob"}, config)
graph.invoke({"messages": "I like dusk,dusk is cute"}, config)
graph.invoke({"messages": "write a short poem about cats"}, config)
graph.invoke({"messages": "now do the same but for dogs"}, config)
graph.invoke({"messages": "what's my name?"}, config)
final_response = graph.invoke({"messages": "what does me like?"}, config)



final_response["messages"][-1].pretty_print()