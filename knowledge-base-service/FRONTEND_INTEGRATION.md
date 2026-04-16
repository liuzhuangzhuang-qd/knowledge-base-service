# 前端对接开发文档（Knowledge Base Service）

本文档用于指导前端页面开发与接口对接，覆盖登录、知识库管理、文档上传、问答、会话历史、反馈全流程。

---

## 1. 基础信息

- Base URL（本地）：`http://localhost:8088`
- 鉴权方式：`Authorization: Bearer <token>`
- 数据格式：除上传接口外，统一 `application/json`

---

## 2. 建议页面结构

推荐按以下页面开发：

1. 登录页
2. 知识库列表页
3. 知识库编辑页（新建/修改）
4. 文档管理页（上传、列表、重建、删除）
5. 问答页（会话式聊天）
6. 会话历史页（会话列表 + 消息详情）

---

## 3. 鉴权与全局请求封装

## 3.1 登录

- 方法：`POST`
- 路径：`/api/auth/login`

请求体：

```json
{
  "username": "alice"
}
```

响应：

```json
{
  "access_token": "xxxxx",
  "token_type": "bearer"
}
```

前端处理建议：

- 登录成功后保存 `access_token`（建议 `localStorage`）。
- 封装统一请求方法，自动在请求头中添加 Bearer Token。

示例（TypeScript）：

```ts
const BASE_URL = "http://localhost:8088";

export async function apiFetch(path: string, init: RequestInit = {}) {
  const token = localStorage.getItem("kb_token");
  const headers = new Headers(init.headers || {});
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}
```

---

## 4. 知识库模块接口

## 4.1 创建知识库

- `POST /api/kbs/create`

请求体：

```json
{
  "name": "产品文档库",
  "visibility": "private"
}
```

响应（KBOut）：

```json
{
  "id": 1,
  "name": "产品文档库",
  "visibility": "private",
  "owner_id": 1
}
```

## 4.2 查询知识库列表

- `GET /api/kbs/getList`
- 响应：`KBOut[]`

## 4.3 查询知识库详情

- `GET /api/kbs/get?kb_id=1`

## 4.4 更新知识库

- `PATCH /api/kbs/update?kb_id=1`

请求体（可选字段）：

```json
{
  "name": "新名称",
  "visibility": "private"
}
```

## 4.5 删除知识库

- `DELETE /api/kbs/delete?kb_id=1`
- 响应：

```json
{
  "ok": true
}
```

---

## 5. 文档模块接口

支持文件类型：`.txt` / `.md` / `.docx`

## 5.1 上传文档

- `POST /api/kbs/upload?kb_id=1`
- `Content-Type: multipart/form-data`
- 字段：`file`

示例（前端）：

```ts
export async function uploadDoc(kbId: number, file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiFetch(`/api/kbs/upload?kb_id=${kbId}`, {
    method: "POST",
    body: form,
  });
}
```

响应（DocumentOut）：

```json
{
  "id": 10,
  "kb_id": 1,
  "title": "intro.docx",
  "status": "pending",
  "metadata_json": {}
}
```

## 5.2 查询知识库文档列表

- `GET /api/kbs/documents/getList?kb_id=1`
- 响应：`DocumentOut[]`

文档状态：

- `pending`：等待处理
- `parsing`：解析中
- `chunking`：切片中
- `embedding`：向量化中
- `ready`：可问答
- `failed`：处理失败（`metadata_json.error` 查看错误）

`ready` 后 `metadata_json` 可能包含：

- `chunk_count`
- `raw_length`
- `normalized_length`
- `dropped_ratio`

## 5.3 查询文档详情

- `GET /api/documents/get?doc_id=10`

## 5.4 重建索引

- `POST /api/documents/update?doc_id=10`
- 响应：`{ "ok": true }`

## 5.5 删除文档

- `DELETE /api/documents/delete?doc_id=10`
- 响应：`{ "ok": true }`

---

## 6. 问答（RAG）接口

## 6.1 发起问答

- `POST /api/kbs/chat?kb_id=1`

请求体：

```json
{
  "question": "系统支持哪些功能？",
  "session_id": 1
}
```

说明：

- `session_id` 可选，不传则自动创建新会话。

响应（ChatResponse）：

```json
{
  "answer": "该系统支持文档上传、解析、检索增强问答等功能。",
  "citations": [
    {
      "docName": "intro.docx",
      "chunk": "......",
      "score": 0.91
    }
  ],
  "usage": {
    "prompt_tokens": 123,
    "completion_tokens": 80,
    "total_tokens": 203
  },
  "sessionId": 1
}
```

前端展示建议：

- 聊天气泡中展示 `answer`
- 在回答下方展示 `citations`（来源文档+片段）
- 可增加“查看引用详情”抽屉

---

## 7. 会话与反馈接口

## 7.1 查询会话列表

- `GET /api/sessions/getList`
- 响应：`SessionOut[]`

`SessionOut` 字段：

- `id`
- `kb_id`
- `user_id`
- `title`
- `created_at`

## 7.2 查询会话消息

- `GET /api/sessions/messages/getList?session_id=1`
- 响应：`MessageOut[]`

`MessageOut` 字段：

- `id`
- `session_id`
- `role`（`user`/`assistant`）
- `content`
- `usage_json`

## 7.3 点赞/点踩

- `POST /api/messages/feedback/create?message_id=100`

请求体：

```json
{
  "is_like": true,
  "note": "回答准确"
}
```

响应：

```json
{
  "ok": true
}
```

---

## 8. 推荐调用时序（前端最小闭环）

1. 登录拿 token
2. 创建知识库（或进入已有知识库）
3. 上传文档
4. 轮询文档列表，直到状态为 `ready`
5. 发起问答
6. 拉取会话消息与历史
7. 对回答进行点赞/点踩

---

## 9. 异常与边界处理建议

通用错误码：

- `400`：参数错误（文件类型、大小等）
- `401`：未登录或 token 失效
- `404`：资源不存在或无权限
- `429`：限流触发
- `500`：服务内部错误

前端建议：

- `401`：清 token，跳转登录页
- `429`：提示“请求过快，请稍后重试”
- 上传后若 `failed`：显示 `metadata_json.error`
- 问答无依据时：给出“未检索到可靠依据”提示并建议优化文档

---

## 10. 联调自测清单

- 能登录并保存 token
- 知识库 CRUD 全流程可用
- 可上传 `.txt/.md/.docx`
- 文档可从 `pending` 到 `ready`
- 可正常问答并返回引用
- 会话列表和消息列表可正确展示
- 点赞/点踩成功写入

