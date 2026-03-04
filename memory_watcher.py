#!/usr/bin/env python3
"""
memory_watcher.py – Local AI Memory for OpenClaw
=================================================

Watches JSONL files in the OpenClaw session directory.
On every change, the latest line is read, converted into a vector
via Ollama, and stored in Qdrant.

Usage:
    python memory_watcher.py
    python memory_watcher.py --sessions-dir /path/to/sessions
    python memory_watcher.py --dry-run   # Parse only, no embedding/storage
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import signal
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

# ── Configuration ──────────────────────────────────────────────────────────

DEFAULT_SESSIONS_DIR = "/home/clawdi/.openclaw/agents/main/sessions/"
OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_EMBED_ENDPOINT = f"{OLLAMA_URL}/api/embed"
EMBED_MODEL = "nomic-embed-text"
EMBED_DIMENSION = 768

QDRANT_HOST = "127.0.0.1"
QDRANT_PORT = 6333
COLLECTION_NAME = "openclaw_memory"

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("memory_watcher")

# ── Helper Classes ──────────────────────────────────────────────────────────


def make_point_id(session_id: str, timestamp: str, text: str) -> str:
    """Creates a deterministic UUID from session_id + timestamp + text hash."""
    raw = f"{session_id}::{timestamp}::{hashlib.sha256(text.encode()).hexdigest()}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def read_last_line(filepath: Path) -> str | None:
    """Efficiently reads the last non-empty line of a file."""
    try:
        with open(filepath, "rb") as f:
            # Seek to end
            f.seek(0, 2)
            file_size = f.tell()
            if file_size == 0:
                return None

            # Read backwards until we have a complete line
            pos = file_size - 1
            lines_found = 0

            while pos > 0:
                f.seek(pos)
                char = f.read(1)
                if char == b"\n":
                    lines_found += 1
                    if lines_found == 1:
                        # First newline from end = end of last line
                        # Keep searching for the start of the last line
                        pass
                    elif lines_found == 2:
                        # Second newline = start of last line
                        break
                pos -= 1

            line = f.readline().decode("utf-8").strip()
            return line if line else None
    except OSError as e:
        log.error("Error reading %s: %s", filepath, e)
        return None


def parse_jsonl_entry(line: str) -> dict[str, Any] | None:
    """Parses a JSONL line and extracts the relevant fields."""
    try:
        data = json.loads(line)
    except json.JSONDecodeError as e:
        log.warning("Invalid JSON: %s", e)
        return None

    # OpenClaw Format: data["message"]["content"] = [{"type": "text", "text": "..."}]
    msg = data.get("message")
    if not isinstance(msg, dict):
        return None

    content_blocks = msg.get("content")
    if not isinstance(content_blocks, list):
        return None

    # Extract all text blocks
    text_parts = []
    for block in content_blocks:
        if isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(block.get("text", ""))

    text = "\n".join(text_parts).strip()
    if not text:
        return None

    sender = msg.get("role") or "unknown"
    timestamp = data.get("timestamp") or datetime.now(timezone.utc).isoformat()

    return {
        "text": text,
        "sender": sender,
        "timestamp": str(timestamp),
    }


# ── Ollama Embedding ───────────────────────────────────────────────────────


def get_embedding(text: str) -> list[float] | None:
    """Creates an embedding via the local Ollama API."""
    try:
        resp = requests.post(
            OLLAMA_EMBED_ENDPOINT,
            json={"model": EMBED_MODEL, "input": text},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        # Ollama /api/embed returns {"embeddings": [[...]]}
        embeddings = data.get("embeddings")
        if embeddings and len(embeddings) > 0:
            return embeddings[0]

        log.error("Unexpected Ollama response: %s", data)
        return None

    except requests.ConnectionError:
        log.error("Ollama not reachable at %s – is the container running?", OLLAMA_URL)
        return None
    except requests.RequestException as e:
        log.error("Ollama error: %s", e)
        return None


# ── Qdrant ──────────────────────────────────────────────────────────────────


class QdrantStore:
    """Manages the Qdrant collection and stores vectors."""

    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT) -> None:
        self.client = QdrantClient(host=host, port=port)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Creates the collection if it does not exist yet."""
        collections = [c.name for c in self.client.get_collections().collections]

        if COLLECTION_NAME not in collections:
            log.info("Creating Qdrant collection '%s' …", COLLECTION_NAME)
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBED_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )
            log.info("Collection '%s' created ✓", COLLECTION_NAME)
        else:
            log.info("Collection '%s' already exists ✓", COLLECTION_NAME)

    def upsert(
        self,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """Stores a point (idempotent via UUID)."""
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )


# ── Watchdog Event Handler ─────────────────────────────────────────────────


class SessionFileHandler(FileSystemEventHandler):
    """Reacts to changes in *.jsonl files."""

    def __init__(self, store: QdrantStore | None, dry_run: bool = False) -> None:
        super().__init__()
        self.store = store
        self.dry_run = dry_run
        self._last_processed: dict[str, str] = {}  # filepath -> last line hash

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._handle(event.src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._handle(event.src_path)

    def _handle(self, filepath_str: str) -> None:
        filepath = Path(filepath_str)

        if filepath.suffix != ".jsonl":
            return

        log.info("Change detected: %s", filepath.name)

        # Read last line
        line = read_last_line(filepath)
        if not line:
            log.debug("File empty or not readable – skipping.")
            return

        # Deduplication: don't process the same line twice
        line_hash = hashlib.md5(line.encode()).hexdigest()
        if self._last_processed.get(str(filepath)) == line_hash:
            log.debug("Line already processed – skipping.")
            return
        self._last_processed[str(filepath)] = line_hash

        # Parse JSON
        entry = parse_jsonl_entry(line)
        if not entry:
            return

        session_id = filepath.stem  # Filename without extension = Session ID
        text = entry["text"]

        log.info(
            "New entry │ Session: %s │ Sender: %s │ Text: %.80s…",
            session_id,
            entry["sender"],
            text,
        )

        if self.dry_run:
            log.info("[DRY RUN] Skipping embedding & storage.")
            return

        # Create embedding
        vector = get_embedding(text)
        if not vector:
            log.error("Embedding failed – entry will not be stored.")
            return

        # Store in Qdrant
        point_id = make_point_id(session_id, entry["timestamp"], text)
        payload = {
            "timestamp": entry["timestamp"],
            "sender": entry["sender"],
            "session_id": session_id,
            "text": text,
        }

        try:
            self.store.upsert(point_id=point_id, vector=vector, payload=payload)
            log.info("Stored in Qdrant ✓  (ID: %s)", point_id[:8])
        except Exception as e:
            log.error("Qdrant error: %s", e)


# ── Main ────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Memory Watcher – Automatically vectorizes OpenClaw chats."
    )
    parser.add_argument(
        "--sessions-dir",
        type=str,
        default=DEFAULT_SESSIONS_DIR,
        help=f"Path to the sessions directory (default: {DEFAULT_SESSIONS_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Watch and parse files only, no embedding/storage.",
    )
    args = parser.parse_args()

    sessions_dir = Path(args.sessions_dir)
    if not sessions_dir.exists():
        log.error("Sessions directory does not exist: %s", sessions_dir)
        log.error("Create it or adjust --sessions-dir.")
        sys.exit(1)

    # ── Connect to Qdrant ────────────────────────────────────────────────
    store: QdrantStore | None = None
    if not args.dry_run:
        try:
            store = QdrantStore()
        except Exception as e:
            log.error("Qdrant not reachable: %s", e)
            log.error("Is the Qdrant container running? Start it with: bash setup.sh")
            sys.exit(1)

        # Ollama Health-Check
        try:
            resp = requests.get(OLLAMA_URL, timeout=5)
            resp.raise_for_status()
            log.info("Ollama reachable ✓")
        except requests.RequestException:
            log.error("Ollama not reachable at %s", OLLAMA_URL)
            log.error("Is the Ollama container running? Start it with: bash setup.sh")
            sys.exit(1)

    # ── Start watcher ────────────────────────────────────────────────────
    handler = SessionFileHandler(store=store, dry_run=args.dry_run)
    observer = Observer()
    observer.schedule(handler, str(sessions_dir), recursive=True)

    log.info("=" * 60)
    log.info("  AI Memory Watcher started")
    log.info("  Watching: %s", sessions_dir)
    if args.dry_run:
        log.info("  Mode: DRY RUN (no embedding/storage)")
    log.info("=" * 60)

    observer.start()

    # Graceful Shutdown
    def shutdown(signum: int, frame: Any) -> None:
        log.info("Shutdown signal received – stopping watcher …")
        observer.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    finally:
        observer.stop()
        observer.join()
        log.info("Watcher stopped. Goodbye! 👋")


if __name__ == "__main__":
    main()
