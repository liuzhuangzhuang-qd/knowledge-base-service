# syntax=docker/dockerfile:1.7
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ARG PIP_EXTRA_INDEX_URL=https://pypi.org/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}
ENV PIP_DEFAULT_TIMEOUT=120
ENV PIP_RETRIES=5

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/data/uploads

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8088"]
