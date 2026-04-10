import uuid

from langchain.embeddings import init_embeddings
from langgraph.store.memory import InMemoryStore

store = InMemoryStore(
    index={
        "embed": init_embeddings("huggingface:Qwen/Qwen3-Embedding-0.6B"),  # Embedding provider
        "dims": 1536,  # Embedding dimensions
        "fields": ["food_preference", "$"]  # Fields to embed
    }
)
user_id = "user123"
namespace_ff = ("pro", "test", user_id)

uni_id2 = str(uuid.uuid4())
testcontent2 = {"food_preference": "I like pizza"}
store.put(namespace_ff, uni_id2, testcontent2, index=["food_preference"])

uni_id = str(uuid.uuid4())
testcontent = {"food_preference": "你好"}
store.put(namespace_ff, uni_id, testcontent, index=False)

store.put(
    namespace_ff,
    str(uuid.uuid4()),
    {
        "food_preference": "I love Italian cuisine",
        "context": "Discussing dinner plans"
    },
    index=["food_preference"]  # Only embed "food_preferences" field
)


sres = store.search(namespace_ff)[-1].dict()

# Find memories about food preferences
# (This can be done after putting memories into the store)
memories = store.search(
    namespace_ff,
    query="What does the user love to eat?",
    limit=2  # Return top 3 matches
)

print(memories)
