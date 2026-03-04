"""
config.py – Central configuration for the Clawdi Brain Dashboard Backend
=========================================================================
All values can be overridden via environment variables.
"""

import os
from pathlib import Path

# ── Qdrant ──────────────────────────────────────────────────────────────────
QDRANT_HOST = os.getenv("QDRANT_HOST", "127.0.0.1")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "openclaw_memory")

# ── FalkorDB ────────────────────────────────────────────────────────────────
FALKOR_HOST = os.getenv("FALKOR_HOST", "127.0.0.1")
FALKOR_PORT = int(os.getenv("FALKOR_PORT", "6379"))
FALKOR_GRAPH = os.getenv("FALKOR_GRAPH", "openclaw_ontology")

# ── Ollama (Embedding) ─────────────────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
EMBED_DIMENSION = int(os.getenv("EMBED_DIMENSION", "768"))

# ── SQLite ──────────────────────────────────────────────────────────────────
SQLITE_PATH = os.getenv(
    "SQLITE_PATH",
    str(Path.home() / ".openclaw" / "short_term.db"),
)

# ── Server ──────────────────────────────────────────────────────────────────
API_PORT = int(os.getenv("API_PORT", "8080"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
