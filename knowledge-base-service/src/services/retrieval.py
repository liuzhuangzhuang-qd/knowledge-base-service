from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.config import settings
from src.models import ChunkEmbedding, Document, DocumentChunk


def vector_retrieve(db: Session, kb_id: int, query_vector: list[float]) -> list[dict]:
    sql = text(
        """
        SELECT
          dc.id AS chunk_id,
          d.title AS doc_name,
          dc.content AS chunk_content,
          1 - (ce.vector <=> CAST(:query_vector AS vector)) AS score
        FROM chunk_embeddings ce
        JOIN document_chunks dc ON dc.id = ce.chunk_id
        JOIN documents d ON d.id = dc.doc_id
        WHERE d.kb_id = :kb_id AND d.status = 'ready'
        ORDER BY ce.vector <=> CAST(:query_vector AS vector)
        LIMIT :topk
        """
    )
    rows = db.execute(
        sql,
        {
            "kb_id": kb_id,
            "query_vector": str(query_vector),
            "topk": settings.retrieval_vector_topk,
        },
    ).mappings()
    return [dict(row) for row in rows]


def keyword_retrieve(db: Session, kb_id: int, query: str) -> list[dict]:
    rows = (
        db.query(DocumentChunk.id, Document.title, DocumentChunk.content)
        .join(Document, Document.id == DocumentChunk.doc_id)
        .filter(Document.kb_id == kb_id, Document.status == "ready")
        .filter(DocumentChunk.content.ilike(f"%{query}%"))
        .limit(settings.retrieval_keyword_topk)
        .all()
    )
    return [
        {
            "chunk_id": row.id,
            "doc_name": row.title,
            "chunk_content": row.content,
            "score": 0.45,
        }
        for row in rows
    ]


def hybrid_retrieve(db: Session, kb_id: int, query: str, query_vector: list[float]) -> list[dict]:
    vec = vector_retrieve(db, kb_id, query_vector)
    kw = keyword_retrieve(db, kb_id, query)
    merged: dict[int, dict] = {}
    for item in vec + kw:
        chunk_id = int(item["chunk_id"])
        existing = merged.get(chunk_id)
        if not existing or item["score"] > existing["score"]:
            merged[chunk_id] = item
    sorted_items = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
    return sorted_items[: settings.rerank_keep_topk]
