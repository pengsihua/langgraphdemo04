import asyncio

from langgraph.store.postgres import AsyncPostgresStore



DB_URI = "postgresql://postgres:123456@localhost:5432/postgres?sslmode=disable"
async def main():
    async with AsyncPostgresStore.from_conn_string(DB_URI) as storetest:
        await storetest.setup()
        namespace=("user","pengsihua")
        # await storetest.aput(namespace, "mem1", {
        #     "text": "喜欢足球",
        #     "type": "hobby",
        #     "level": 1
        # })
        #
        # await storetest.aput(namespace, "mem2", {
        #     "text": "喜欢AI",
        #     "type": "hobby",
        #     "level": 2
        # })
        #
        # await storetest.aput(namespace, "mem3", {
        #     "text": "工作内容",
        #     "type": "work",
        #     "level": 1
        # })
        ff = await storetest.asearch(namespace)
        print(ff)


asyncio.run(main(),loop_factory=asyncio.SelectorEventLoop)