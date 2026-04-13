def split_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == length:
            break
        start = max(0, end - overlap)

    return chunks
