import re

from rank_bm25 import BM25Okapi

from retriever.store import get_all_chunks


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def keyword_search(query: str, k: int = 5, where: dict | None = None) -> list[dict]:
    """Search by exact words (BM25). Returns evidence items sorted by score."""
    chunks = get_all_chunks(where)
    query_words = _tokenize(query)
    if not chunks or not query_words:
        return []

    tokens = [_tokenize(c["content"]) for c in chunks]
    scores = BM25Okapi(tokens).get_scores(query_words)

    # BM25 can give a score of 0 or less when the collection is very small,
    # so we keep every chunk that really shares a word with the query
    matches = [i for i in range(len(chunks)) if set(query_words) & set(tokens[i])]
    matches.sort(key=lambda i: scores[i], reverse=True)

    items = []
    for i in matches[:k]:
        items.append({
            "document": chunks[i]["document"],
            "page": chunks[i]["page"],
            "score": round(float(scores[i]), 3),
            "content": chunks[i]["content"],
        })
    return items
