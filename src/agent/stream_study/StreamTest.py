from typing import NotRequired

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.func import task
from typing_extensions import TypedDict
from langchain_core.utils.uuid import uuid7

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
import requests


# Define a TypedDict to represent the state
class State(TypedDict):
    url: str
    result: NotRequired[str]

@task
def get_request(url: str):
    print("只打印第一次")
    return requests.get(url).text[:100]

def call_api(state: State):
    """Example node that makes an API request."""
    print("每次打印")
    result = get_request(state['url']).result()
    print(result)
    return {
        "result": result
    }


# Create a StateGraph builder and add a node for the call_api function
builder = StateGraph(State)
builder.add_node("call_api", call_api)

# Connect the start and end nodes to the call_api node
builder.add_edge(START, "call_api")
builder.add_edge("call_api", END)

# Specify a checkpointer
with SqliteSaver.from_conn_string("checkpoint.db") as checkpointer:
    # Compile the graph with the checkpointer
    graph = builder.compile(checkpointer=checkpointer)

    # Define a config with a thread ID.
    thread_id =  str(uuid7())
    config = {"configurable": {"thread_id": thread_id}}

    # Invoke the graph
    #out1  = graph.invoke({"url": "https://httpbin.org/get?mma=texyy"}, config)

    #print("结果1：",out1["result"])


    # print("\n=== 第二次运行（恢复）===")
    # out2 = graph.invoke(None, config)  # 输入 None = 恢复
    # print("结果2:", out2["result"])


    for chunk in graph.stream(
            {"topic": "ice cream","url": "https://httpbin.org/get?mma=tey"},
            stream_mode=["updates", "custom"],
            version="v2",
            config=config
    ):
        if chunk["type"] == "updates":
            for node_name, state in chunk["data"].items():
                print(f"节点 {node_name} 已更新：{state}")
        elif chunk["type"] == "custom":
            print(f"状态：{chunk['data']['status']}")
