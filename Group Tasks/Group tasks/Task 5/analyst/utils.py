def format_evidence(evidence: list[dict]) -> str:
    if not evidence:
        return "(no evidence)"
    parts = []
    for i, e in enumerate(evidence, start=1):
        parts.append(f'[{i}] {e["document"]}, page {e["page"]}:\n{e["content"]}')
    return "\n\n".join(parts)


def clean_evidence(evidence) -> tuple[list[dict], list[str]]:
    """Keep only the items that have document, page and content. Returns (items, warnings)."""
    good, warnings = [], []
    for i, e in enumerate(evidence or [], start=1):
        ok = (isinstance(e, dict) and e.get("document") and e.get("page") not in (None, "")
              and isinstance(e.get("content"), str) and e["content"].strip())
        if ok:
            good.append(e)
        else:
            warnings.append(f"Evidence item {i} was ignored because document, page or content is missing.")
    return good, warnings
