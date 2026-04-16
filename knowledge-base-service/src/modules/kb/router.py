from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.security import get_current_user
from src.models import KnowledgeBase, User
from src.schemas import KBCreate, KBOut, KBUpdate


router = APIRouter(prefix="/knownAPI/api/kbs", tags=["knowledge-base"])


@router.post("/create", response_model=KBOut)
def create_kb(
    payload: KBCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    kb = KnowledgeBase(name=payload.name, visibility=payload.visibility, owner_id=user.id)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return kb


@router.get("/getList", response_model=list[KBOut])
def list_kbs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(KnowledgeBase).filter(KnowledgeBase.owner_id == user.id).all()


@router.get("/get", response_model=KBOut)
def get_kb(kb_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    kb = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id)
        .first()
    )
    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")
    return kb


@router.patch("/update", response_model=KBOut)
def update_kb(
    kb_id: int,
    payload: KBUpdate,
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
    if payload.name is not None:
        kb.name = payload.name
    if payload.visibility is not None:
        kb.visibility = payload.visibility
    db.commit()
    db.refresh(kb)
    return kb


@router.delete("/delete")
def delete_kb(
    kb_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    kb = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id)
        .first()
    )
    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")
    db.delete(kb)
    db.commit()
    return {"ok": True}
