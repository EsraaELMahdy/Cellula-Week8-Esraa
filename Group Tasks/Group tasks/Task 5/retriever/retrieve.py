from retriever.context_selector import select_context
from retriever.keyword import keyword_search
from retriever.metadata_filter import build_filter
from retriever.query_rewriter import rewrite_query
from retriever.reranker import rerank
from retriever.store import semantic_search


def retrieve(question: str, history: list | None = None,
             extra_query: str | None = None, max_chunks: int = 5) -> list[dict]:
    """Find the best chunks for a question.

    Returns a list of {"document", "page", "score", "content"}.
    """
    if not question or not question.strip():
        raise ValueError("The question is empty.")

    query = extra_query or rewrite_query(question, history)
    where = build_filter(question)

    candidates = []
    seen = set()
    for r in semantic_search(query, k=10, where=where) + keyword_search(query, k=10, where=where):
        key = (r["document"], r["page"], r["content"])
        if key not in seen:
            seen.add(key)
            candidates.append(r)

    ranked = rerank(query, candidates)
    return select_context(ranked, max_chunks=max_chunks)
