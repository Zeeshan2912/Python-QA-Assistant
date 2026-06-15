from qdrant_client import QdrantClient
client = QdrantClient(":memory:")
print("QdrantClient attributes:")
attrs = dir(client)
for attr in attrs:
    if "search" in attr.lower() or "query" in attr.lower() or "upsert" in attr.lower():
        print(f"- {attr}")
