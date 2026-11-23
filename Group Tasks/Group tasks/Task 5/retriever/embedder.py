from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            _model = TextEmbedding(model_name=MODEL_NAME)
        except Exception as e:
            raise RuntimeError(
                f"Could not load the embedding model {MODEL_NAME}. "
                f"The first run needs internet to download it. ({e})"
            ) from e
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Convert a list of texts to a list of vectors."""
    return [v.tolist() for v in _get_model().embed(texts)]
