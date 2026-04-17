import asyncio
from dataclasses import dataclass

from langchain.embeddings import init_embeddings
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.postgres import AsyncPostgresStore, PostgresStore

DB_URI = "postgresql://postgres:123456@localhost:5432/postgres?sslmode=disable"

model = init_chat_model(model="glm-5",
                        model_provider="openai",
                        api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                        tags=["joke"]
                        )

# Create store with semantic search enabled
# embeddings = init_embeddings("openai:text-embedding-3-small")
embed_mode = init_embeddings("huggingface:Qwen/Qwen3-Embedding-0.6B")
with PostgresStore.from_conn_string(
        DB_URI,
        index={
            "embed": embed_mode,
            "dims": 1024,
            "fields": ["text", "$"],
        }) as syncStore:
    syncStore.setup()
    syncStore.put(("user_123", "memories"), "1", {"text": "I love pizza"}, index=["text"])
    syncStore.put(("user_123", "memories"), "2", {"text": "I am a plumber"}, index=["text"])


@dataclass
class Context:
    user_id: str


async def chat(state: MessagesState, runtime: Runtime[Context]):
    # Search based on user's last message
    user_id=runtime.context.user_id
    items = await runtime.store.asearch(
        (user_id, "memories"), query=state["messages"][-1].content, limit=1
    )
    memories = "\n".join(item.value["text"] for item in items)
    memories = f"## Memories of user\n{memories}" if memories else ""
    print(memories)
    response = await model.ainvoke(
        [
            {"role": "system", "content": f"You are a helpful assistant.\n{memories}"},
            *state["messages"],
        ]
    )
    return {"messages": [response]}


async def main():
    async with(
        AsyncPostgresStore.from_conn_string(
            DB_URI,
            index={
                "embed": embed_mode,
                "dims": 1536,
                "fields": ["text", "$"],
            }) as store,
        AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer,
    ):
        builder = StateGraph(MessagesState)
        builder.add_node(chat)
        builder.add_edge(START, "chat")
        graph = builder.compile(checkpointer=checkpointer, store=store)

        async for chunk in graph.astream(
                input={"messages": [{"role": "user", "content": "I'm hungry"}]},
                config={"configurable": {
                    "thread_id": "2134"
                }},
                context=Context(user_id="user_123", ),
                stream_mode="messages",
                version='v2'
        ):
            if chunk.get("type") == "messages":
                message_chunk, metadata = chunk["data"]
                print(metadata)
                if message_chunk.content:
                    print(message_chunk.content)



asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)
