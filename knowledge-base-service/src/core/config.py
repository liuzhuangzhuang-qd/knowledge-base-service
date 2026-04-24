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

    def _read_qwen_csv_kv(self) -> dict[str, str]:
        candidate_files = [
            Path("qianwen-apiKey.csv"),
            Path("/app/qianwen-apiKey.csv"),
            Path(__file__).resolve().parents[2] / "qianwen-apiKey.csv",
        ]

        kv: dict[str, str] = {}
        for key_file in candidate_files:
            if not key_file.exists():
                continue
            for line in key_file.read_text(encoding="utf-8").splitlines():
                if not line.strip() or "," not in line:
                    continue
                key, value = line.split(",", 1)
                k = key.strip()
                v = value.strip()
                if k and v:
                    kv[k] = v
            if kv:
                break
        return kv

    def resolve_qwen_api_key(self) -> str:
        if self.qwen_api_key.strip():
            return self.qwen_api_key.strip()

        kv = self._read_qwen_csv_kv()
        if kv.get("apiKey"):
            return kv["apiKey"]
        return ""

    def resolve_qwen_base_url(self) -> str:
        kv = self._read_qwen_csv_kv()
        if (
            kv.get("openAiCompatible")
            and self.qwen_base_url.strip() == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ):
            return kv["openAiCompatible"]
        return self.qwen_base_url


settings = Settings()
