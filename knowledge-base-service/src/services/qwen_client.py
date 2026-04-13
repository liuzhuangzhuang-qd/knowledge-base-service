from openai import OpenAI

from src.core.config import settings


def _client() -> OpenAI:
    api_key = settings.resolve_qwen_api_key()
    if not api_key:
        raise RuntimeError("QWEN_API_KEY is empty")
    return OpenAI(api_key=api_key, base_url=settings.qwen_base_url)


def embed_texts(texts: list[str]) -> list[list[float]]:
    cli = _client()
    resp = cli.embeddings.create(model=settings.qwen_embed_model, input=texts)
    return [item.embedding for item in resp.data]


def chat_with_context(question: str, contexts: list[str]) -> tuple[str, dict]:
    cli = _client()
    system_prompt = (
        "你是知识库问答助手。仅依据提供的检索片段回答。"
        "如果证据不足，请直接回答：未检索到可靠依据。"
        "回答时保持简洁，并优先引用事实。"
    )
    context_text = "\n\n".join([f"[{i+1}] {c}" for i, c in enumerate(contexts)])
    user_prompt = f"问题：{question}\n\n检索片段：\n{context_text}"
    resp = cli.chat.completions.create(
        model=settings.qwen_chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )
    answer = resp.choices[0].message.content or "未检索到可靠依据。"
    usage = {
        "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0),
        "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
        "total_tokens": getattr(resp.usage, "total_tokens", 0),
    }
    return answer, usage
