from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.security import create_access_token
from src.models import User
from src.schemas import LoginRequest, TokenResponse


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
        user = User(username=payload.username, role="owner")
        db.add(user)
        db.commit()
    token = create_access_token(subject=payload.username)
    return TokenResponse(access_token=token)
