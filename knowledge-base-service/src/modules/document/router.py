import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.db import get_db
from src.core.security import get_current_user
from src.models import Document, KnowledgeBase, User
from src.schemas import DocumentOut
from src.workers.document_tasks import process_document


router = APIRouter(tags=["documents"])


@router.post("/api/kbs/{kb_id}/documents", response_model=DocumentOut)
def upload_document(
    kb_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kb = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id)
        .first()
    )
    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")

    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".txt", ".md"}:
        raise HTTPException(status_code=400, detail="Only .txt and .md are allowed in MVP")

    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, f"{uuid.uuid4()}{ext}")
    with open(file_path, "wb") as out:
        out.write(file.file.read())

    doc = Document(
        kb_id=kb_id,
        title=file.filename or "untitled",
        file_path=file_path,
        status="pending",
        metadata_json={},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(process_document, doc.id)
    return doc


@router.get("/api/kbs/{kb_id}/documents", response_model=list[DocumentOut])
def list_documents(
    kb_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    kb = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id)
        .first()
    )
    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")
    return db.query(Document).filter(Document.kb_id == kb_id).all()


@router.get("/api/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = (
        db.query(Document)
        .join(KnowledgeBase, KnowledgeBase.id == Document.kb_id)
        .filter(Document.id == doc_id, KnowledgeBase.owner_id == user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/api/documents/{doc_id}/reindex")
def reindex_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = (
        db.query(Document)
        .join(KnowledgeBase, KnowledgeBase.id == Document.kb_id)
        .filter(Document.id == doc_id, KnowledgeBase.owner_id == user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = "pending"
    db.commit()
    background_tasks.add_task(process_document, doc.id)
    return {"ok": True}


@router.delete("/api/documents/{doc_id}")
def delete_document(
    doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    doc = (
        db.query(Document)
        .join(KnowledgeBase, KnowledgeBase.id == Document.kb_id)
        .filter(Document.id == doc_id, KnowledgeBase.owner_id == user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return {"ok": True}
