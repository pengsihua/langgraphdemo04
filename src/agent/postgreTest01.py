import asyncio
from dataclasses import dataclass

from langgraph.store.memory import InMemoryStore


from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver

from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState
from langgraph.runtime import Runtime

import uuid

store = InMemoryStore()

@dataclass
class Context:
    user_id: str


def update_memory(state: MessagesState, runtime: Runtime[Context]):
    # Get the user id from the runtime context
    user_id = runtime.context.user_id
    print("step1")
    # Namespace the memory
    namespace = (user_id, "memories")

    # ... Analyze conversation and create a new memory

    # Create a new memory ID
    memory_id = str(uuid.uuid4())

    # We create a new memory
    runtime.store.put(namespace, memory_id, {"memory": "update_memory"})
    return {"messages": [{"role": "user", "content": "hello"}]}


def call_model(state: MessagesState, runtime: Runtime[Context]):
    # Get the user id from the runtime context
    print("step2")
    user_id = runtime.context.user_id
    # Namespace the memory
    namespace = (user_id, "memories")

    # Search based on the most recent message
    memories = runtime.store.search(
        namespace,
        query=state["messages"][-1].content,
        limit=3
    )
    info = "\n".join([d.value["memory"] for d in memories])

    print(info)
    # ... Use memories in the model call
    return {"messages": [{"role": "user", "content": "sdwewtre"}]}


builder = StateGraph(MessagesState, context_schema=Context)

builder.add_node("call_model", call_model)
builder.add_node("update_memory", update_memory)
builder.add_edge(START, "update_memory")
builder.add_edge("update_memory", "call_model")

DB_URI = "postgres://postgres:123456@localhost:5432/postgres?sslmode=disable"

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    graph = builder.compile(checkpointer=checkpointer, store=store)

    # Invoke the graph
    config = {"configurable": {"thread_id": "2"}}

    # First let's just say hi to the AI
    for update in graph.stream(
            {"messages": [{"role": "user", "content": "hi"}]},
            config,
            stream_mode="updates",
            context=Context(user_id="user123"),
    ):
        print("update:", update)
