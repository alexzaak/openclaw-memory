import os
import sys
import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "127.0.0.1")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "openclaw_memory")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

query = sys.argv[1]
resp = requests.post(
    f"{OLLAMA_URL}/api/embed",
    json={"model": EMBED_MODEL, "input": query},
)
vector = resp.json()["embeddings"][0]

results = client.query_points(
    collection_name=QDRANT_COLLECTION,
    query=vector,
    limit=15,
)

for point in results.points:
    date = point.payload.get('timestamp', '')[:10]
    print(f"[{date}] [{point.payload.get('sender')}] {point.payload.get('text')}")
