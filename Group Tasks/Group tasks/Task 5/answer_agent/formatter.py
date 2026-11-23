"""Part C: citation, source and response formatting."""

def format_sources(evidence):
    sources = []
    seen = set()
    for item in evidence or []:
        document, page = item.get("document"), item.get("page")
        if not document or page is None:
            continue
        key = (str(document), str(page))
        if key in seen:
            continue
        seen.add(key)
        sources.append({"document": str(document), "page": page,
                        "citation": f"[{document}, p. {page}]"})
    return sources


def format_citations(evidence):
    return " ".join(source["citation"] for source in format_sources(evidence))


def format_response(answer, sources, sufficient, warnings=None):
    return {"answer": answer.strip(), "sources": sources,
            "enough_evidence": bool(sufficient), "warnings": warnings or []}
