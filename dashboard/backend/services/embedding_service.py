"""
embedding_service.py – Ollama Embedding Client
"""

import logging
import requests
from config import OLLAMA_URL, EMBED_MODEL

log = logging.getLogger("embedding_service")

EMBED_ENDPOINT = f"{OLLAMA_URL}/api/embed"


def get_embedding(text: str) -> list[float] | None:
    """Generate an embedding vector via the local Ollama API."""
    try:
        resp = requests.post(
            EMBED_ENDPOINT,
            json={"model": EMBED_MODEL, "input": text},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings")
        if embeddings and len(embeddings) > 0:
            return embeddings[0]
        log.error("Unexpected Ollama response: %s", data)
        return None
    except requests.ConnectionError:
        log.error("Ollama unreachable at %s", OLLAMA_URL)
        return None
    except requests.RequestException as e:
        log.error("Ollama error: %s", e)
        return None
