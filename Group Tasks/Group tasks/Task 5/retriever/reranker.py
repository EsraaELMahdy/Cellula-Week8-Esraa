from fastembed.rerank.cross_encoder import TextCrossEncoder

MODEL_NAME = "Xenova/ms-marco-MiniLM-L-6-v2"
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            _model = TextCrossEncoder(model_name=MODEL_NAME)
        except Exception as e:
            raise RuntimeError(
                f"Could not load the reranker model {MODEL_NAME}. "
                f"The first run needs internet to download it. ({e})"
            ) from e
    return _model


def rerank(query: str, candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []
    scores = list(_get_model().rerank(query, [c["content"] for c in candidates]))
    results = []
    for item, score in zip(candidates, scores):
        new_item = dict(item)
        new_item["score"] = round(float(score), 3)
        results.append(new_item)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
