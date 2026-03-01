import sys
import requests
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient(host="127.0.0.1", port=6333)

query = sys.argv[1]
resp = requests.post(
    "http://127.0.0.1:11434/api/embed",
    json={"model": "nomic-embed-text", "input": query},
)
vector = resp.json()["embeddings"][0]

results = client.query_points(
    collection_name="openclaw_memory",
    query=vector,
    limit=15,
)

for point in results.points:
    date = point.payload.get('timestamp', '')[:10]
    print(f"[{date}] [{point.payload.get('sender')}] {point.payload.get('text')}")
