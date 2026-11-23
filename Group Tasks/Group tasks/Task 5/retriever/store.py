import os
from pathlib import Path

import chromadb

from retriever.embedder import embed

DB_PATH = os.getenv("CHROMA_DB_PATH") or str(Path(__file__).resolve().parent.parent / "chroma_db")
_col = None


def _get_col():
    global _col
    if _col is None:
        try:
            client = chromadb.PersistentClient(path=DB_PATH)
            _col = client.get_or_create_collection(
                "documents", metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            raise RuntimeError(f"Could not open ChromaDB at {DB_PATH}: {e}") from e
    return _col


def add_chunks(chunks: list[dict]) -> None:
    """Store the chunks of one document. Uploading the same document again replaces its old chunks."""
    if not chunks:
        raise ValueError("There are no chunks to store.")
    name = chunks[0]["document"]
    texts = [c["text"] for c in chunks]

    # embed first: if this fails, the old version of the document is still safe
    vectors = embed(texts)

    col = _get_col()
    try:
        col.delete(where={"document": name})  # only this document, not the others
        col.add(
            ids=[c["chunk_id"] for c in chunks],
            documents=texts,
            embeddings=vectors,
            metadatas=[{"document": c["document"], "page": c["page"]} for c in chunks],
        )
    except Exception as e:
        raise RuntimeError(f"ChromaDB error while saving {name}: {e}") from e


def _make_item(text, meta, score=None) -> dict | None:
    """Build an evidence item. Returns None if the metadata is broken."""
    if not meta or "document" not in meta or "page" not in meta or not text:
        return None
    item = {"document": meta["document"], "page": meta["page"], "content": text}
    if score is not None:
        item["score"] = score
    return item


def semantic_search(query: str, k: int = 5, where: dict | None = None) -> list[dict]:
    """Search by meaning. Returns evidence items sorted by score (higher = better)."""
    col = _get_col()
    try:
        total = col.count()
        if total == 0:
            return []
        res = col.query(
            query_embeddings=embed([query]),
            n_results=min(k, total),
            where=where,
        )
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"ChromaDB error while searching: {e}") from e

    items = []
    for text, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        item = _make_item(text, meta, round(1 - dist, 3))
        if item:
            items.append(item)
    return items


def get_all_chunks(where: dict | None = None) -> list[dict]:
    """Return every stored chunk (used by keyword search)."""
    try:
        data = _get_col().get(where=where, include=["documents", "metadatas"])
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"ChromaDB error while reading chunks: {e}") from e

    items = []
    for text, meta in zip(data["documents"], data["metadatas"]):
        item = _make_item(text, meta)
        if item:
            items.append(item)
    return items


def list_documents() -> list[str]:
    """Names of all stored documents."""
    try:
        data = _get_col().get(include=["metadatas"])
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"ChromaDB error while reading documents: {e}") from e
    return sorted({m["document"] for m in data["metadatas"] if m and "document" in m})
