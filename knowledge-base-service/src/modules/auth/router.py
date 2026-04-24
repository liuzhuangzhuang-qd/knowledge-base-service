from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.security import create_access_token
from src.models import User
from src.schemas import LoginRequest, RegisterRequest, TokenResponse


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existed_user = db.query(User).filter(User.username == payload.username).first()
    if existed_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(username=payload.username, password=payload.password, role="owner")
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"ok": True}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.username == payload.username, User.password == payload.password)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
        )

    token = create_access_token(subject=user.username)
    return TokenResponse(access_token=token)
