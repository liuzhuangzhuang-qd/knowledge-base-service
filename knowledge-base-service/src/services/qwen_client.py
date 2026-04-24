from openai import APIConnectionError, OpenAI

from src.core.config import settings


_DASHSCOPE_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def _client(base_url: str | None = None) -> OpenAI:
    api_key = settings.resolve_qwen_api_key()
    if not api_key:
        raise RuntimeError("QWEN_API_KEY is empty")
    return OpenAI(
        api_key=api_key,
        base_url=base_url or settings.resolve_qwen_base_url(),
        timeout=60.0,
        max_retries=1,
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    primary_base_url = settings.resolve_qwen_base_url()
    try:
        cli = _client(primary_base_url)
        resp = cli.embeddings.create(model=settings.qwen_embed_model, input=texts)
        return [item.embedding for item in resp.data]
    except APIConnectionError as exc:
        # Retry once using DashScope default endpoint for better compatibility.
        if primary_base_url != _DASHSCOPE_DEFAULT_BASE_URL:
            try:
                cli = _client(_DASHSCOPE_DEFAULT_BASE_URL)
                resp = cli.embeddings.create(model=settings.qwen_embed_model, input=texts)
                return [item.embedding for item in resp.data]
            except APIConnectionError as retry_exc:
                raise RuntimeError(
                    "Qwen connection failed. Tried custom and default base_url, "
                    "please check network/DNS and endpoint availability."
                ) from retry_exc
        raise RuntimeError(
            "Qwen connection failed. Please check QWEN_BASE_URL network accessibility."
        ) from exc


def chat_with_context(question: str, contexts: list[str]) -> tuple[str, dict]:
    system_prompt = (
        "你是知识库问答助手。仅依据提供的检索片段回答。"
        "如果证据不足，请直接回答：未检索到可靠依据。"
        "回答时保持简洁，并优先引用事实。"
    )
    context_text = "\n\n".join([f"[{i+1}] {c}" for i, c in enumerate(contexts)])
    user_prompt = f"问题：{question}\n\n检索片段：\n{context_text}"
    primary_base_url = settings.resolve_qwen_base_url()
    try:
        cli = _client(primary_base_url)
        resp = cli.chat.completions.create(
            model=settings.qwen_chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
    except APIConnectionError as exc:
        if primary_base_url != _DASHSCOPE_DEFAULT_BASE_URL:
            try:
                cli = _client(_DASHSCOPE_DEFAULT_BASE_URL)
                resp = cli.chat.completions.create(
                    model=settings.qwen_chat_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                )
            except APIConnectionError as retry_exc:
                raise RuntimeError(
                    "Qwen connection failed. Tried custom and default base_url, "
                    "please check network/DNS and endpoint availability."
                ) from retry_exc
        else:
            raise RuntimeError(
                "Qwen connection failed. Please check QWEN_BASE_URL network accessibility."
            ) from exc
    answer = resp.choices[0].message.content or "未检索到可靠依据。"
    usage = {
        "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0),
        "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
        "total_tokens": getattr(resp.usage, "total_tokens", 0),
    }
    return answer, usage
