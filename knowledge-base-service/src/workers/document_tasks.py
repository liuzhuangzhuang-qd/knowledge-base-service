from sqlalchemy.orm import Session

from src.core.db import SessionLocal
from src.models import ChunkEmbedding, Document, DocumentChunk
from src.services.chunking import split_text
from src.services.qwen_client import embed_texts


def process_document(doc_id: int) -> None:
    db: Session = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            return

        document.status = "parsing"
        db.commit()

        with open(document.file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

        document.status = "chunking"
        db.commit()
        chunks = split_text(raw_text)

        db.query(ChunkEmbedding).filter(
            ChunkEmbedding.chunk_id.in_(
                db.query(DocumentChunk.id).filter(DocumentChunk.doc_id == doc_id)
            )
        ).delete(synchronize_session=False)
        db.query(DocumentChunk).filter(DocumentChunk.doc_id == doc_id).delete(
            synchronize_session=False
        )
        db.commit()

        created_chunks: list[DocumentChunk] = []
        for i, content in enumerate(chunks):
            c = DocumentChunk(doc_id=doc_id, chunk_index=i, content=content)
            db.add(c)
            created_chunks.append(c)
        db.commit()

        document.status = "embedding"
        db.commit()
        vectors = embed_texts([c.content for c in created_chunks]) if created_chunks else []
        for c, vec in zip(created_chunks, vectors):
            db.add(ChunkEmbedding(chunk_id=c.id, vector=vec))
        db.commit()

        document.status = "ready"
        document.metadata_json = {
            "chunk_count": len(created_chunks),
        }
        db.commit()
    except Exception as exc:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            document.status = "failed"
            document.metadata_json = {"error": str(exc)}
            db.commit()
    finally:
        db.close()
