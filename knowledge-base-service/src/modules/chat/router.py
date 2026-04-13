from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.security import get_current_user
from src.models import (
    AnswerCitation,
    ChatMessage,
    ChatSession,
    KnowledgeBase,
    User,
)
from src.schemas import ChatRequest, ChatResponse, CitationOut
from src.services.qwen_client import chat_with_context, embed_texts
from src.services.retrieval import hybrid_retrieve


router = APIRouter(tags=["chat"])


@router.post("/api/kbs/{kb_id}/chat", response_model=ChatResponse)
def chat(
    kb_id: int,
    payload: ChatRequest,
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

    session = None
    if payload.session_id:
        session = (
            db.query(ChatSession)
            .filter(
                ChatSession.id == payload.session_id,
                ChatSession.user_id == user.id,
                ChatSession.kb_id == kb_id,
            )
            .first()
        )
    if not session:
        session = ChatSession(kb_id=kb_id, user_id=user.id, title=payload.question[:30])
        db.add(session)
        db.commit()
        db.refresh(session)

    user_msg = ChatMessage(session_id=session.id, role="user", content=payload.question, usage_json={})
    db.add(user_msg)
    db.commit()

    query_vec = embed_texts([payload.question])[0]
    retrieved = hybrid_retrieve(db, kb_id, payload.question, query_vec)
    contexts = [item["chunk_content"] for item in retrieved]

    if not contexts:
        answer_text = "未检索到可靠依据。"
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    else:
        answer_text, usage = chat_with_context(payload.question, contexts)

    assistant_msg = ChatMessage(
        session_id=session.id, role="assistant", content=answer_text, usage_json=usage
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    citations: list[CitationOut] = []
    for item in retrieved:
        citation = AnswerCitation(
            message_id=assistant_msg.id,
            chunk_id=item["chunk_id"],
            score=float(item["score"]),
            doc_name=item["doc_name"],
            snippet=item["chunk_content"][:200],
        )
        db.add(citation)
        citations.append(
            CitationOut(
                docName=item["doc_name"],
                chunk=item["chunk_content"][:200],
                score=float(item["score"]),
            )
        )
    db.commit()

    return ChatResponse(answer=answer_text, citations=citations, usage=usage, sessionId=session.id)
