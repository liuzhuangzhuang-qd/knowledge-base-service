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

2) 首次构建并启动：

```bash
docker compose build api
docker compose up -d
```

3) 后续启动（不重复构建镜像）：

```bash
docker compose up -d
```

4) 健康检查：

```bash
GET http://localhost:8088/health
```

## 2. 主要接口

### 鉴权

- `POST /api/auth/login`  
  body: `{ "username": "alice" }`  
  返回 bearer token

### 知识库

- `POST /api/kbs/create`
- `GET /api/kbs/getList`
- `GET /api/kbs/get?kb_id={id}`
- `PATCH /api/kbs/update?kb_id={id}`
- `DELETE /api/kbs/delete?kb_id={id}`

### 文档

- `POST /api/kbs/upload?kb_id={id}`（multipart，MVP 支持 `.txt/.md`）
- `GET /api/kbs/documents/getList?kb_id={id}`
- `GET /api/documents/get?doc_id={docId}`
- `POST /api/documents/update?doc_id={docId}`（重建索引）
- `DELETE /api/documents/delete?doc_id={docId}`

### 问答

- `POST /api/kbs/chat?kb_id={id}`
  - 入参：`question`, `session_id(可选)`
  - 返回：`answer`, `citations[]`, `usage`, `sessionId`

### 会话与反馈

- `GET /api/sessions/getList`
- `GET /api/sessions/messages/getList?session_id={id}`
- `POST /api/messages/feedback/create?message_id={id}`

## 3. 架构说明（当前实现）

- `api`: FastAPI 对外接口
- `db`: PostgreSQL + pgvector
- `background tasks`: FastAPI 后台任务处理 ingest/chunk/embed

检索策略为：

- 向量检索 topK（默认 12）
- 关键词补充 topK（默认 10）
- 合并去重后保留前 N（默认 5）入模

## 4. 项目结构（规范版）

```text
knowledge-base-service/
  src/
    core/                    # 基础设施层：配置、数据库连接、鉴权
    modules/                 # 接口层：按业务域拆分路由
      auth/                  # 登录鉴权
      kb/                    # 知识库 CRUD
      document/              # 文档上传/查询/重建/删除
      chat/                  # RAG 问答
      feedback/              # 会话列表、消息列表、反馈
    services/                # 领域服务层：切片、检索、模型调用
    workers/                 # 后台任务：文档处理 pipeline
    main.py                  # FastAPI 应用入口
    models.py                # SQLAlchemy 数据模型
    schemas.py               # Pydantic 请求/响应模型
  data/                      # 本地上传文件与运行数据（开发环境）
  docker-compose.yml         # 本地/服务器编排（api + db）
  Dockerfile                 # API 镜像构建定义
  requirements.txt           # Python 依赖清单
  API.md                     # 对外接口规范文档
  DOCKER.md                  # Docker 部署与运维文档
  README.md                  # 项目说明与快速上手
```

目录分层约定：

- `core`：框架与基础能力，不放业务逻辑。
- `modules`：仅处理路由、参数校验、鉴权依赖与返回格式。
- `services`：承载可复用业务能力，避免在路由层堆积逻辑。
- `workers`：异步/后台处理流程，与在线请求链路解耦。

## 5. 说明与下一步建议

- 当前为 MVP，默认单用户 owner 视角，便于先打通闭环。
- 已包含访问控制（`kb.owner_id`）和上传大小/类型限制。
- 建议下一步：
  - 增加真实多成员 RBAC（owner/editor/viewer）
  - 支持 PDF/DOCX 解析器
  - 增加 Alembic 迁移、OpenTelemetry、评测脚本
  - 为检索加入 rerank 模型

## 6. 开发规范（建议落地）

### 6.1 新增业务模块目录模板

在 `src/modules/<domain>/` 下创建路由模块，保持最小结构：

```text
src/modules/<domain>/
  __init__.py
  router.py
```

约定：

- `<domain>` 使用小写英文（如 `kb`、`document`、`feedback`）。
- 每个域只维护一个 `router.py` 入口，避免同域多入口分散。

### 6.2 分层职责约束

- `modules`：仅放路由与请求处理（参数、鉴权、响应组装）。
- `services`：承载可复用业务逻辑（检索、切片、模型调用等）。
- `workers`：后台任务与耗时处理流程，不阻塞主请求。
- `core`：配置、数据库、鉴权等基础能力。
- `models.py` / `schemas.py`：分别维护 ORM 模型与接口模型。

### 6.3 路由命名规范

统一前缀：

- 统一使用 `/api/...`

CRUD 命名：

- 创建：`/create`
- 列表：`/getList`
- 详情：`/get`
- 更新：`/update`
- 删除：`/delete`

参数约定：

- 资源主键优先使用 query 参数传递，例如：
  - `kb_id`
  - `doc_id`
  - `session_id`
  - `message_id`

示例：

- `POST /api/kbs/create`
- `GET /api/kbs/getList`
- `GET /api/kbs/get?kb_id={id}`
- `PATCH /api/kbs/update?kb_id={id}`
- `DELETE /api/kbs/delete?kb_id={id}`

### 6.4 命名与代码风格

- 文件名、目录名使用小写 + 下划线风格。
- 函数命名采用动词开头，语义明确（如 `create_kb`、`list_documents`）。
- 同一类响应尽量返回统一结构（成功返回对象/数组，操作返回 `{ "ok": true }`）。
- 新增接口时，必须同步更新 `API.md` 与 `README.md` 的接口章节。
