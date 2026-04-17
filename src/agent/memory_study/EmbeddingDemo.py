from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:9000/v1",
    api_key="sk-no-key-needed"  # 随便填
)

response = client.embeddings.create(
    model="text-embedding-qwen3",
    input="我在本地用Qwen3生成向量"
)

# 向量
vec = response.data[0].embedding
print(len(vec))  # 1024


embeddings = OpenAIEmbeddings(
    openai_api_base="http://127.0.0.1:9000/v1",  # 你的本地API
    openai_api_key="fghfgh",
    model="text-embedding-qwen3"
)

# 测试生成向量
query_embedding = embeddings.embed_query("这是本地Qwen3生成的向量")
print("向量长度:", len(query_embedding))  # 输出 1024
print(query_embedding)