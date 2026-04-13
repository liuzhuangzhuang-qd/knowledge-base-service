# Knowledge Base Service (MVP -> Scalable)

FastAPI + PostgreSQL(pgvector) 的知识库后端，支持：

- 知识库 CRUD
- 文档上传与异步解析/切片/向量化
- RAG 问答（返回引用）
- 会话历史与反馈
- 基础鉴权（单租户 token）

## 1. 快速启动（Docker）

1) 准备配置：

- 已提供 `.env`（本地可直接跑）
- 将千问 key 放到以下任一位置：
  - `.env` 的 `QWEN_API_KEY=你的key`
  - 或根目录 `qianwen-apiKey.csv`（服务会自动读取第一列）

2) 启动：

```bash
docker compose up --build
```

3) 健康检查：

```bash
GET http://localhost:8088/health
```

## 2. 主要接口

### 鉴权

- `POST /api/auth/login`  
  body: `{ "username": "alice" }`  
  返回 bearer token

### 知识库

- `POST /api/kbs`
- `GET /api/kbs`
- `GET /api/kbs/{id}`
- `PATCH /api/kbs/{id}`
- `DELETE /api/kbs/{id}`

### 文档

- `POST /api/kbs/{id}/documents`（multipart，MVP 支持 `.txt/.md`）
- `GET /api/kbs/{id}/documents`
- `GET /api/documents/{docId}`
- `POST /api/documents/{docId}/reindex`
- `DELETE /api/documents/{docId}`

### 问答

- `POST /api/kbs/{id}/chat`
  - 入参：`question`, `session_id(可选)`
  - 返回：`answer`, `citations[]`, `usage`, `sessionId`

### 会话与反馈

- `GET /api/sessions`
- `GET /api/sessions/{id}/messages`
- `POST /api/messages/{id}/feedback`

## 3. 架构说明（当前实现）

- `api`: FastAPI 对外接口
- `db`: PostgreSQL + pgvector
- `background tasks`: FastAPI 后台任务处理 ingest/chunk/embed

检索策略为：

- 向量检索 topK（默认 12）
- 关键词补充 topK（默认 10）
- 合并去重后保留前 N（默认 5）入模

## 4. 项目结构

```text
src/
  modules/
    auth/
      router.py
    kb/
      router.py
    document/
      router.py
    chat/
      router.py
    feedback/
      router.py
  core/
    config.py
    db.py
    security.py
  services/
    chunking.py
    retrieval.py
    qwen_client.py
  workers/
    document_tasks.py
  models.py
  schemas.py
  main.py
```

## 5. 说明与下一步建议

- 当前为 MVP，默认单用户 owner 视角，便于先打通闭环。
- 已包含访问控制（`kb.owner_id`）和上传大小/类型限制。
- 建议下一步：
  - 增加真实多成员 RBAC（owner/editor/viewer）
  - 支持 PDF/DOCX 解析器
  - 增加 Alembic 迁移、OpenTelemetry、评测脚本
  - 为检索加入 rerank 模型
