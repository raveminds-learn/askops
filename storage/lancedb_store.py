"""
storage/lancedb_store.py
Stores and semantically searches log data using LanceDB + Ollama embeddings.
"""
import hashlib
from pathlib import Path
from typing import Optional

import lancedb
import pyarrow as pa
from langchain_community.embeddings import OllamaEmbeddings

DB_PATH = Path(__file__).parent.parent / "lancedb"
EMBED_MODEL = "nomic-embed-text"
VECTOR_DIM = 768

_embedder = None
_db = None


def get_embedder() -> OllamaEmbeddings:
    global _embedder
    if _embedder is None:
        _embedder = OllamaEmbeddings(model=EMBED_MODEL)
    return _embedder


def get_db():
    global _db
    if _db is None:
        _db = lancedb.connect(str(DB_PATH))
    return _db


def get_or_create_table():
    db = get_db()
    if "logs" in db.table_names():
        return db.open_table("logs")
    schema = pa.schema([
        pa.field("id",          pa.string()),
        pa.field("trade_id",    pa.string()),
        pa.field("source",      pa.string()),
        pa.field("severity",    pa.string()),
        pa.field("timestamp",   pa.string()),
        pa.field("service",     pa.string()),
        pa.field("content",     pa.string()),
        pa.field("content_hash",pa.string()),
        pa.field("vector",      pa.list_(pa.float32(), VECTOR_DIM)),
    ])
    return db.create_table("logs", schema=schema)


def ingest_logs(logs: list[dict]) -> int:
    """
    Ingest a list of log dicts into LanceDB.
    Skips duplicates based on content hash.
    Returns number of new records inserted.
    """
    table = get_or_create_table()
    embedder = get_embedder()
    inserted = 0

    existing_df = table.to_pandas() if table.count_rows() > 0 else None
    existing_hashes = set(existing_df["content_hash"].tolist()) if existing_df is not None else set()

    rows = []
    for log in logs:
        content = log.get("content", log.get("message", ""))
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if content_hash in existing_hashes:
            continue
        rows.append({
            "id":           log.get("id", content_hash[:12]),
            "trade_id":     str(log.get("trade_id", "")),
            "source":       log.get("source", "datadog"),
            "severity":     log.get("level", log.get("severity", "INFO")),
            "timestamp":    str(log.get("timestamp", "")),
            "service":      log.get("service", ""),
            "content":      content,
            "content_hash": content_hash,
            "vector":       embedder.embed_query(content),
        })
        existing_hashes.add(content_hash)
        inserted += 1

    if rows:
        table.add(rows)
    return inserted


def search(query: str, trade_id: Optional[str] = None, top_k: int = 5) -> list[dict]:
    """
    Semantic search over stored logs.
    Optionally filter by trade_id.
    """
    table = get_or_create_table()
    if table.count_rows() == 0:
        return []

    embedder = get_embedder()
    query_vector = embedder.embed_query(query)

    search_query = table.search(query_vector).limit(top_k * 3)

    results = search_query.to_pandas()

    if trade_id and not results.empty:
        filtered = results[results["trade_id"] == str(trade_id)]
        if not filtered.empty:
            results = filtered

    return results.head(top_k).to_dict(orient="records")
