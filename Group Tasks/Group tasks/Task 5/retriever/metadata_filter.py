import re

from retriever.store import list_documents


def build_filter(question: str) -> dict | None:
    """If the question mentions a file name or a page number, limit the search to it."""
    q = question.lower()
    conditions = []

    for name in list_documents():
        if name.lower() in q:
            conditions.append({"document": name})
            break

    match = re.search(r"(?:page|صفحة|صفحه)\s*(\d+)", q)
    if match:
        conditions.append({"page": int(match.group(1))})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}
