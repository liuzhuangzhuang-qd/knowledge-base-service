# 知识库服务接口文档（MVP）

Base URL（本地）: `http://localhost:8088`

鉴权方式：`Authorization: Bearer <token>`

---

## 1. 认证

### 1.1 登录（简化）

- **POST** `/api/auth/login`
- **说明**：若用户不存在会自动创建，返回 token

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

---

## 2. 知识库（KB）

### 2.1 创建知识库

- **POST** `/api/kbs`

请求体：

```json
{
  "name": "产品文档库",
  "visibility": "private"
}
```

响应：

```json
{
  "id": 1,
  "name": "产品文档库",
  "visibility": "private",
  "owner_id": 1
}
```

### 2.2 查询知识库列表

- **GET** `/api/kbs`

响应：`KBOut[]`

### 2.3 查询知识库详情

- **GET** `/api/kbs/{id}`

### 2.4 更新知识库

- **PATCH** `/api/kbs/{id}`

请求体（可部分更新）：

```json
{
  "name": "新名称",
  "visibility": "private"
}
```

### 2.5 删除知识库

- **DELETE** `/api/kbs/{id}`

响应：

```json
{
  "ok": true
}
```

---

## 3. 文档

> MVP 仅支持 `.txt` / `.md`

### 3.1 上传文档

- **POST** `/api/kbs/{id}/documents`
- `Content-Type: multipart/form-data`
- 字段：`file`

响应示例：

```json
{
  "id": 10,
  "kb_id": 1,
  "title": "intro.md",
  "status": "pending",
  "metadata_json": {}
}
```

文档状态流转：

- `pending` -> `parsing` -> `chunking` -> `embedding` -> `ready`
- 失败：`failed`（错误信息在 `metadata_json.error`）

### 3.2 查询知识库文档列表

- **GET** `/api/kbs/{id}/documents`

### 3.3 查询文档详情

- **GET** `/api/documents/{docId}`

### 3.4 重建索引

- **POST** `/api/documents/{docId}/reindex`

响应：

```json
{
  "ok": true
}
```

### 3.5 删除文档

- **DELETE** `/api/documents/{docId}`

响应：

```json
{
  "ok": true
}
```

---

## 4. 问答（RAG）

### 4.1 发起问答

- **POST** `/api/kbs/{id}/chat`

请求体：

```json
{
  "question": "系统支持哪些功能？",
  "session_id": 1
}
```

> `session_id` 可选，不传则自动创建新会话。

响应示例：

```json
{
  "answer": "该系统支持文档上传、解析、检索增强问答等功能。",
  "citations": [
    {
      "docName": "intro.md",
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

---

## 5. 会话与反馈

### 5.1 查询会话列表

- **GET** `/api/sessions`

### 5.2 查询会话消息

- **GET** `/api/sessions/{id}/messages`

### 5.3 点赞/点踩

- **POST** `/api/messages/{id}/feedback`

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

## 6. 通用响应与错误码

- 200/201：成功
- 400：参数错误（如文件类型/大小不符合）
- 401：token 无效或缺失
- 404：资源不存在或无权限
- 429：限流触发
- 500：服务内部异常

常见错误体：

```json
{
  "detail": "KB not found"
}
```

---

## 7. 调用顺序建议（最小闭环）

1. 登录拿 token  
2. 创建知识库  
3. 上传文档  
4. 轮询文档状态到 `ready`  
5. 调用 chat  
6. 查看会话消息并提交反馈
