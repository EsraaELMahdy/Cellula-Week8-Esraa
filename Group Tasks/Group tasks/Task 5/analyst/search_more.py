from retriever.retrieve import retrieve


def search_more(question: str, query: str, evidence: list[dict],
                history: list | None = None) -> tuple[list[dict], int]:
    """Ask the Retriever for more specific evidence.

    Returns (all evidence, number of new chunks added). Chunks we already have are not added again.
    """
    new_items = retrieve(question, history=history, extra_query=query)

    all_items = list(evidence)
    seen = {(e["document"], e["page"], e["content"]) for e in all_items}
    added = 0
    for item in new_items:
        key = (item["document"], item["page"], item["content"])
        if key not in seen:
            seen.add(key)
            all_items.append(item)
            added += 1
    return all_items, added
