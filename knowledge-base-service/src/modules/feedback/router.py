from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.security import get_current_user
from src.models import ChatMessage, ChatSession, Feedback, User
from src.schemas import FeedbackIn, MessageOut, SessionOut


router = APIRouter(tags=["sessions-feedback"])


@router.get("/knownAPI/api/sessions/getList", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )


@router.get("/knownAPI/api/sessions/messages/getList", response_model=list[MessageOut])
def list_messages(
    session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


@router.post("/knownAPI/api/messages/feedback/create")
def create_feedback(
    message_id: int,
    payload: FeedbackIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    msg = (
        db.query(ChatMessage)
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .filter(ChatMessage.id == message_id, ChatSession.user_id == user.id)
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    fb = Feedback(
        message_id=message_id,
        user_id=user.id,
        is_like=payload.is_like,
        note=payload.note,
    )
    db.add(fb)
    db.commit()
    return {"ok": True}
