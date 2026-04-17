import asyncio
import sys
from dataclasses import dataclass
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.runtime import Runtime
import uuid

model = init_chat_model(model="glm-5",
                          model_provider="openai",
                          api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                          base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                          tags=["joke"]
                          )


@dataclass
class Context:
    user_id: str


async def call_model(
        state: MessagesState,
        runtime: Runtime[Context],
):
    user_id = runtime.context.user_id
    namespace = ("memories", user_id)
    #memories = await runtime.store.asearch(namespace, query=str(state["messages"][-1].content))
    memories = await runtime.store.asearch(namespace, query=str("sdfdsfdfds"))
    info = "\n".join([d.value["data"] for d in memories])
    print("info:",info)
    system_msg = f"You are a helpful assistant talking to the user. User info: {info}"

    # Store new memories if the user asks the model to remember
    last_message = state["messages"][-1]
    if "remember" in last_message.content.lower():
        memory = "User name is Bob"
        await runtime.store.aput(namespace, str(uuid.uuid4()), {"data": "啦啦啦啦啦"})

    response = await model.ainvoke(
        [{"role": "system", "content": system_msg}] + state["messages"]
    )
    return {"messages": response}


DB_URI = "postgresql://postgres:123456@localhost:5432/postgres?sslmode=disable"


async def main():
    async with (
        AsyncPostgresStore.from_conn_string(DB_URI) as store,
        AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer,
    ):
        await store.setup()
        await checkpointer.setup()

        builder = StateGraph(MessagesState, context_schema=Context)
        builder.add_node(call_model)
        builder.add_edge(START, "call_model")

        graph = builder.compile(
            checkpointer=checkpointer,
            store=store,
        )

        config = {"configurable": {"thread_id": "11"}}
        async for chunk in graph.astream(
                {"messages": [{"role": "user", "content": "Hi! Remember: 辣辣辣辣"}]},
                config,
                stream_mode="values",
                context=Context(user_id="1"),
        ):
            chunk["messages"][-1].pretty_print()

        config = {"configurable": {"thread_id": "22"}}
        async for chunk in graph.astream(
                {"messages": [{"role": "user", "content": "what is my name?"}]},
                config,
                stream_mode="values",
                context=Context(user_id="1"),
        ):
            chunk["messages"][-1].pretty_print()


async def background():
    dfd = await  main()
    print(dfd)

asyncio.run(background(),loop_factory=  asyncio.SelectorEventLoop)



print("主函数1")
print("主函数2")