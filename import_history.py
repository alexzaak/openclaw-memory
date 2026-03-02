import json
import os
import glob
from pathlib import Path
from memory_watcher import parse_jsonl_entry, get_embedding, make_point_id, QdrantStore
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-7s │ %(message)s")
log = logging.getLogger("import")

def import_all():
    store = QdrantStore()
    sessions_dir = "/home/clawdi/.openclaw/agents/main/sessions/"
    files = glob.glob(os.path.join(sessions_dir, "*.jsonl"))
    
    total_processed = 0
    total_skipped = 0
    
    for filepath_str in files:
        filepath = Path(filepath_str)
        session_id = filepath.stem
        log.info(f"Processing session: {session_id}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                entry = parse_jsonl_entry(line)
                if not entry:
                    total_skipped += 1
                    continue
                    
                text = entry["text"]
                # Skip very short or empty texts to save time
                if len(text) < 2:
                    total_skipped += 1
                    continue
                    
                vector = get_embedding(text)
                if not vector:
                    log.warning(f"Failed to get embedding for text: {text[:30]}")
                    total_skipped += 1
                    continue
                    
                point_id = make_point_id(session_id, entry["timestamp"], text)
                payload = {
                    "timestamp": entry["timestamp"],
                    "sender": entry["sender"],
                    "session_id": session_id,
                    "text": text,
                }
                
                store.upsert(point_id=point_id, vector=vector, payload=payload)
                total_processed += 1
                
                if total_processed % 100 == 0:
                    log.info(f"Imported {total_processed} points so far...")

    log.info(f"Import complete! Processed: {total_processed}, Skipped: {total_skipped}")

if __name__ == '__main__':
    import_all()
