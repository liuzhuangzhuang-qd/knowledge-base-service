from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.config import settings
from src.core.db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default="owner")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    visibility: Mapped[str] = mapped_column(String(32), default="private")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kb_id: Mapped[int] = mapped_column(ForeignKey("knowledge_bases.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"
    __table_args__ = (UniqueConstraint("chunk_id", name="uq_embedding_chunk_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id"), index=True)
    vector: Mapped[list[float]] = mapped_column(Vector(settings.vector_dim))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kb_id: Mapped[int] = mapped_column(ForeignKey("knowledge_bases.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="New Session")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    usage_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AnswerCitation(Base):
    __tablename__ = "answer_citations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("chat_messages.id"), index=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    doc_name: Mapped[str] = mapped_column(String(255))
    snippet: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedbacks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("chat_messages.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    is_like: Mapped[bool] = mapped_column(Boolean)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
