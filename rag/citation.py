def build_citations(documents: list) -> list[dict]:
    """
    Extract citation information from retrieved documents.
    """

    citations = []

    seen = set()

    for document in documents:

        metadata = document.metadata

        source_url = metadata.get("source_url")
        scheme_id = metadata.get("scheme_id")
        scheme_name = metadata.get("scheme_name")
        section = metadata.get("section")
        chunk_id = metadata.get("chunk_id")

        if not source_url:
            continue

        citation_key = (
            scheme_id,
            chunk_id,
            source_url
        )

        if citation_key in seen:
            continue

        seen.add(citation_key)

        citations.append({
            "scheme_id": scheme_id,
            "scheme_name": scheme_name,
            "section": section,
            "chunk_id": chunk_id,
            "source_url": source_url
        })

    return citations