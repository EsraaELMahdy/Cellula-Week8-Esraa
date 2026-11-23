"""Person A integration: keep the Week 7 pipeline and add explicit extractive mode."""
import os
import re
from threading import RLock
from pathlib import Path

_lock = RLock()
_pages = []


def mode():
    return os.getenv("APP_MODE", "llm")


def ingest_pages(pages):
    if mode() == "extractive":
        with _lock:
            names = {p["document"] for p in pages}
            _pages[:] = [p for p in _pages if p["document"] not in names] + list(pages)
        return len(pages)
    from retriever.chunker import chunk_pages
    from retriever.store import add_chunks
    chunks = chunk_pages(pages)
    if not chunks:
        raise ValueError("No readable text found.")
    add_chunks(chunks)
    return len(chunks)


def ingest_document(path):
    from retriever.loader import load_file
    pages = load_file(str(path))
    if not any(p["text"].strip() for p in pages):
        raise ValueError("No readable text. Use the image OCR flow for scanned pages.")
    return ingest_pages(pages)


def answer(question, history):
    if mode() == "extractive":
        words = set(re.findall(r"\w+", question.lower()))
        with _lock:
            ranked = sorted(_pages, key=lambda p: len(words & set(re.findall(r"\w+", p["text"].lower()))), reverse=True)
            selected = [dict(p) for p in ranked[:3] if words & set(re.findall(r"\w+", p["text"].lower()))]
        sources = [{"document": p["document"], "page": p["page"]} for p in selected]
        text = "\n\n".join(f'{p["text"][:1800]} [{p["document"]}, p. {p["page"]}]' for p in selected)
        return {"answer": text or "No matching evidence found in the uploaded sources.",
                "analysis": "Extractive mode returns matching source passages; no LLM reasoning was performed.",
                "sources": sources, "enough_evidence": False, "results": {},
                "warnings": ["Extractive demo mode. Matching passages do not establish answer sufficiency."]}
    from orchestrator import run_workflow
    return run_workflow(question, history=history)
