from dataclasses import dataclass
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langgraph.runtime import Runtime
import uuid

# 模型配置
model = init_chat_model(
    model="glm-5",
    model_provider="openai",
    api_key="sk-1f87f2a8548e479f9d1a75973554786b",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


@dataclass
class Context:
    user_id: str


def call_model(state: MessagesState, runtime: Runtime[Context]):
    user_id = runtime.context.user_id
    namespace = ("memories", user_id)
    memories = runtime.store.search(namespace, query=str(state["messages"][-1].content))
    info = "\n".join([d.value["data"] for d in memories]) if memories else "No memories"

    if "remember" in state["messages"][-1].content.lower():
        runtime.store.put(namespace, str(uuid.uuid4()), {"data": "User name is Bob"})

    response = model.invoke([{"role": "system", f"content": info}] + state["messages"])
    return {"messages": response}


DB_URI = "postgresql://postgres:123456@localhost:5432/postgres?sslmode=disable"

# ==========================================
# ✅ 核心修复：必须先 setup，再使用
# ==========================================
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # 强制初始化表结构
    checkpointer.setup()

    with PostgresStore.from_conn_string(DB_URI) as store:
        # 强制初始化表结构
        store.setup()

        builder = StateGraph(MessagesState, context_schema=Context)
        builder.add_node("call_model", call_model)
        builder.add_edge(START, "call_model")

        graph = builder.compile(
            checkpointer=checkpointer,
            store=store,
        )

        # ======================
        # 第一次请求
        # ======================
        config = {"configurable": {"thread_id": "pg1"}}
        for chunk in graph.stream(
                {"messages": [{"role": "user", "content": "Hi! Remember my name is Bob"}]},
                config,
                stream_mode="values",
                context=Context(user_id="1"),
        ):
            chunk["messages"][-1].pretty_print()

        # ======================
        # 第二次请求（读记忆）
        # ======================
        config = {"configurable": {"thread_id": "pg1"}}
        for chunk in graph.stream(
                {"messages": [{"role": "user", "content": "What is my name?"}]},
                config,
                stream_mode="values",
                context=Context(user_id="1"),
        ):
            chunk["messages"][-1].pretty_print()