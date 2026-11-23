def _words(text: str) -> set[str]:
    return set(text.lower().split())


def select_context(items: list[dict], max_chunks: int = 5) -> list[dict]:
    selected = []
    for item in items:
        words = _words(item["content"])
        duplicate = False
        for kept in selected:
            kept_words = _words(kept["content"])
            overlap = len(words & kept_words) / max(len(words | kept_words), 1)
            if overlap > 0.8:
                duplicate = True
                break
        if not duplicate:
            selected.append(item)
        if len(selected) == max_chunks:
            break
    return selected