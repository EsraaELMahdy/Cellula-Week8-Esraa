from retriever.chunker import chunk_pages
from retriever.loader import load_file
from retriever.store import add_chunks


def ingest_file(path: str) -> int:
    """Load a file, split it into chunks and save them. Returns the number of chunks."""
    chunks = chunk_pages(load_file(path))
    if not chunks:
        raise ValueError(f"No readable text in {path} (is it a scanned PDF or an empty file?)")
    add_chunks(chunks)
    return len(chunks)
