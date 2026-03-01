from qdrant_client import QdrantClient
import requests
import json

client = QdrantClient(host="127.0.0.1", port=6333)

# Suchtext → Embedding
query = "Apfelkuchen"
resp = requests.post(
    "http://127.0.0.1:11434/api/embed",
    json={"model": "nomic-embed-text", "input": query},
)
vector = resp.json()["embeddings"][0]

# Suche in Qdrant
results = client.query_points(
    collection_name="openclaw_memory",
    query=vector,
    limit=5,
)

for point in results.points:
    print(f"[{point.payload['sender']}] {point.payload['text'][:100]}")
