from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "knowledge-base-service"
    app_env: str = "dev"
    secret_key: str = "replace_me_secret"
    access_token_expire_minutes: int = 1440

    database_url: str = "postgresql+psycopg2://kb_user:kb_pass@localhost:5432/kb_service"
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 20

    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_chat_model: str = "qwen-plus"
    qwen_embed_model: str = "text-embedding-v3"

    vector_dim: int = 1024
    retrieval_vector_topk: int = 12
    retrieval_keyword_topk: int = 10
    rerank_keep_topk: int = 5

    def resolve_qwen_api_key(self) -> str:
        if self.qwen_api_key.strip():
            return self.qwen_api_key.strip()

        key_file = Path("qianwen-apiKey.csv")
        if key_file.exists():
            content = key_file.read_text(encoding="utf-8").strip()
            if content:
                return content.split(",")[0].strip()
        return ""


settings = Settings()
