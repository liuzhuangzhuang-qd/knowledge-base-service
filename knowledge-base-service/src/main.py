import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.core.config import settings
from src.core.db import init_db
from src.modules.auth.router import router as auth_router
from src.modules.chat.router import router as chat_router
from src.modules.document.router import router as document_router
from src.modules.feedback.router import router as session_feedback_router
from src.modules.kb.router import router as kb_router


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title=settings.app_name)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def ratelimit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


@app.middleware("http")
async def request_trace_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Elapsed-Ms"] = str(elapsed_ms)
    return response


@app.on_event("startup")
def startup_event():
    os.makedirs(settings.upload_dir, exist_ok=True)
    init_db()


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(auth_router)
app.include_router(kb_router)
app.include_router(document_router)
app.include_router(chat_router)
app.include_router(session_feedback_router)
