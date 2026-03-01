#!/usr/bin/env python3
"""
memory_watcher.py – Lokales AI-Gedächtnis für OpenClaw
======================================================

Überwacht JSONL-Dateien im OpenClaw-Session-Verzeichnis.
Bei jeder Änderung wird die neueste Zeile gelesen, über Ollama
in einen Vektor umgewandelt und in Qdrant gespeichert.

Nutzung:
    python memory_watcher.py
    python memory_watcher.py --sessions-dir /pfad/zu/sessions
    python memory_watcher.py --dry-run   # Nur parsen, kein Embedding/Storage
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

# ── Konfiguration ──────────────────────────────────────────────────────────

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

# ── Hilfsklassen ────────────────────────────────────────────────────────────


def make_point_id(session_id: str, timestamp: str, text: str) -> str:
    """Erzeugt eine deterministische UUID aus session_id + timestamp + text-Hash."""
    raw = f"{session_id}::{timestamp}::{hashlib.sha256(text.encode()).hexdigest()}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def read_last_line(filepath: Path) -> str | None:
    """Liest effizient die letzte nicht-leere Zeile einer Datei."""
    try:
        with open(filepath, "rb") as f:
            # Zum Ende springen
            f.seek(0, 2)
            file_size = f.tell()
            if file_size == 0:
                return None

            # Rückwärts lesen bis wir eine vollständige Zeile haben
            pos = file_size - 1
            lines_found = 0

            while pos > 0:
                f.seek(pos)
                char = f.read(1)
                if char == b"\n":
                    lines_found += 1
                    if lines_found == 1:
                        # Erste Newline von hinten = Ende der letzten Zeile
                        # Weiter suchen nach dem Start der letzten Zeile
                        pass
                    elif lines_found == 2:
                        # Zweite Newline = Start der letzten Zeile
                        break
                pos -= 1

            line = f.readline().decode("utf-8").strip()
            return line if line else None
    except OSError as e:
        log.error("Fehler beim Lesen von %s: %s", filepath, e)
        return None


def parse_jsonl_entry(line: str) -> dict[str, Any] | None:
    """Parst eine JSONL-Zeile und extrahiert die relevanten Felder."""
    try:
        data = json.loads(line)
    except json.JSONDecodeError as e:
        log.warning("Ungültiges JSON: %s", e)
        return None

    # OpenClaw Format: data["message"]["content"] = [{"type": "text", "text": "..."}]
    msg = data.get("message")
    if not isinstance(msg, dict):
        return None

    content_blocks = msg.get("content")
    if not isinstance(content_blocks, list):
        return None

    # Extrahiere alle Text-Blöcke
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
    """Erzeugt ein Embedding über die lokale Ollama-API."""
    try:
        resp = requests.post(
            OLLAMA_EMBED_ENDPOINT,
            json={"model": EMBED_MODEL, "input": text},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        # Ollama /api/embed gibt {"embeddings": [[...]]} zurück
        embeddings = data.get("embeddings")
        if embeddings and len(embeddings) > 0:
            return embeddings[0]

        log.error("Unerwartete Ollama-Antwort: %s", data)
        return None

    except requests.ConnectionError:
        log.error("Ollama nicht erreichbar unter %s – läuft der Container?", OLLAMA_URL)
        return None
    except requests.RequestException as e:
        log.error("Ollama-Fehler: %s", e)
        return None


# ── Qdrant ──────────────────────────────────────────────────────────────────


class QdrantStore:
    """Verwaltet die Qdrant-Collection und speichert Vektoren."""

    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT) -> None:
        self.client = QdrantClient(host=host, port=port)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Legt die Collection an, falls sie noch nicht existiert."""
        collections = [c.name for c in self.client.get_collections().collections]

        if COLLECTION_NAME not in collections:
            log.info("Erstelle Qdrant-Collection '%s' …", COLLECTION_NAME)
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBED_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )
            log.info("Collection '%s' erstellt ✓", COLLECTION_NAME)
        else:
            log.info("Collection '%s' existiert bereits ✓", COLLECTION_NAME)

    def upsert(
        self,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """Speichert einen Punkt (idempotent via UUID)."""
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
    """Reagiert auf Änderungen an *.jsonl-Dateien."""

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

        log.info("Änderung erkannt: %s", filepath.name)

        # Letzte Zeile lesen
        line = read_last_line(filepath)
        if not line:
            log.debug("Datei leer oder nicht lesbar – überspringe.")
            return

        # Deduplizierung: gleiche Zeile nicht doppelt verarbeiten
        line_hash = hashlib.md5(line.encode()).hexdigest()
        if self._last_processed.get(str(filepath)) == line_hash:
            log.debug("Zeile bereits verarbeitet – überspringe.")
            return
        self._last_processed[str(filepath)] = line_hash

        # JSON parsen
        entry = parse_jsonl_entry(line)
        if not entry:
            return

        session_id = filepath.stem  # Dateiname ohne Endung = Session-ID
        text = entry["text"]

        log.info(
            "Neuer Eintrag │ Session: %s │ Sender: %s │ Text: %.80s…",
            session_id,
            entry["sender"],
            text,
        )

        if self.dry_run:
            log.info("[DRY RUN] Überspringe Embedding & Storage.")
            return

        # Embedding erzeugen
        vector = get_embedding(text)
        if not vector:
            log.error("Embedding fehlgeschlagen – Eintrag wird nicht gespeichert.")
            return

        # In Qdrant speichern
        point_id = make_point_id(session_id, entry["timestamp"], text)
        payload = {
            "timestamp": entry["timestamp"],
            "sender": entry["sender"],
            "session_id": session_id,
            "text": text,
        }

        try:
            self.store.upsert(point_id=point_id, vector=vector, payload=payload)
            log.info("Gespeichert in Qdrant ✓  (ID: %s)", point_id[:8])
        except Exception as e:
            log.error("Qdrant-Fehler: %s", e)


# ── Main ────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Memory Watcher – Vektorisiert OpenClaw-Chats automatisch."
    )
    parser.add_argument(
        "--sessions-dir",
        type=str,
        default=DEFAULT_SESSIONS_DIR,
        help=f"Pfad zum Sessions-Verzeichnis (Standard: {DEFAULT_SESSIONS_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Dateien überwachen und parsen, kein Embedding/Storage.",
    )
    args = parser.parse_args()

    sessions_dir = Path(args.sessions_dir)
    if not sessions_dir.exists():
        log.error("Sessions-Verzeichnis existiert nicht: %s", sessions_dir)
        log.error("Erstelle es oder passe --sessions-dir an.")
        sys.exit(1)

    # ── Qdrant verbinden ────────────────────────────────────────────────
    store: QdrantStore | None = None
    if not args.dry_run:
        try:
            store = QdrantStore()
        except Exception as e:
            log.error("Qdrant nicht erreichbar: %s", e)
            log.error("Läuft der Qdrant-Container? Starte ihn mit: bash setup.sh")
            sys.exit(1)

        # Ollama Health-Check
        try:
            resp = requests.get(OLLAMA_URL, timeout=5)
            resp.raise_for_status()
            log.info("Ollama erreichbar ✓")
        except requests.RequestException:
            log.error("Ollama nicht erreichbar unter %s", OLLAMA_URL)
            log.error("Läuft der Ollama-Container? Starte ihn mit: bash setup.sh")
            sys.exit(1)

    # ── Watcher starten ─────────────────────────────────────────────────
    handler = SessionFileHandler(store=store, dry_run=args.dry_run)
    observer = Observer()
    observer.schedule(handler, str(sessions_dir), recursive=True)

    log.info("=" * 60)
    log.info("  AI Memory Watcher gestartet")
    log.info("  Überwache: %s", sessions_dir)
    if args.dry_run:
        log.info("  Modus: DRY RUN (kein Embedding/Storage)")
    log.info("=" * 60)

    observer.start()

    # Graceful Shutdown
    def shutdown(signum: int, frame: Any) -> None:
        log.info("Shutdown-Signal empfangen – beende Watcher …")
        observer.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    finally:
        observer.stop()
        observer.join()
        log.info("Watcher beendet. Auf Wiedersehen! 👋")


if __name__ == "__main__":
    main()
