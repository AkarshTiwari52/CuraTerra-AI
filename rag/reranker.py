from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_reranker = None


def get_reranker():
    global _reranker

    if _reranker is None:
        _reranker = CrossEncoder(MODEL_NAME)

    return _reranker


def rerank_documents(
    query,
    documents,
    top_k=5,
    score_threshold=None
):
    """
    Rerank documents using a cross-encoder.

    If score_threshold is None, documents are ranked
    and the top_k are returned without score filtering.
    """

    if not documents:
        return []

    reranker = get_reranker()

    pairs = [
        (query, document.page_content)
        for document in documents
    ]

    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(documents, scores),
        key=lambda x: float(x[1]),
        reverse=True
    )

    results = []

    for document, score in ranked:

        score = float(score)

        if (
            score_threshold is not None
            and score < score_threshold
        ):
            continue

        results.append({
            "document": document,
            "score": score
        })

    return results[:top_k]