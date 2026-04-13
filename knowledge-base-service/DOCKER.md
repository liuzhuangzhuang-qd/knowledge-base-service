# Docker 运行文档（本地 + 服务器）

本文档说明如何在本地开发机和远程服务器运行 `knowledge-base-service`。

---

## 1. 前置要求

- 已安装 Docker
- 已安装 Docker Compose（`docker compose`）
- 机器可访问千问 API（若要使用问答）

> 若你的 Docker 默认镜像源对 `docker.io` 返回 403（常见于部分镜像加速配置），本项目已在 `docker-compose.yml` 中为数据库使用可访问镜像地址。

---

## 2. 环境变量配置

项目根目录有 `.env`，关键配置如下：

- `DATABASE_URL=postgresql+psycopg2://kb_user:kb_pass@db:5432/kb_service`
- `QWEN_API_KEY=你的千问key`
- `QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `QWEN_CHAT_MODEL=qwen-plus`
- `QWEN_EMBED_MODEL=text-embedding-v3`

> 也支持从根目录 `qianwen-apiKey.csv` 自动读取 key（第一列）。

---

## 3. 本地运行（Windows/macOS/Linux）

在项目根目录执行：

```bash
docker compose up --build
```

后台运行：

```bash
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs -f api
```

停止服务：

```bash
docker compose down
```

连同数据卷一起清理（谨慎）：

```bash
docker compose down -v
```

健康检查：

```bash
curl http://localhost:8088/health
```

---

## 4. 服务器部署（云主机/内网主机）

以下示例为 Linux 服务器。

### 4.1 拉取代码

```bash
git clone <your-repo-url>
cd knowledge-base-service
```

### 4.2 配置生产环境变量

编辑 `.env`：

- 修改 `SECRET_KEY` 为强随机字符串
- 设置 `QWEN_API_KEY`
- 如需暴露外网，确认端口策略（默认 8088）

### 4.3 启动

```bash
docker compose up -d --build
```

### 4.4 防火墙与安全组

开放必要端口：

- `8088`（API 对外可访问时）

默认不建议暴露：

- `5432`（PostgreSQL）

若需要外部数据库，请修改 `docker-compose.yml` 和 `.env`。

---

## 5. 网络访问方式

### 5.1 本机访问

- `http://localhost:8088/health`

### 5.2 局域网访问

- `http://<服务器IP>:8088/health`

### 5.3 域名访问（推荐）

建议在 Nginx/Caddy 前置反向代理并启用 HTTPS：

- `https://api.example.com`

同时建议加上：

- 请求超时设置
- 限流
- 访问日志与错误日志

---

## 6. 运维常用命令

重启：

```bash
docker compose restart api
```

仅更新应用镜像：

```bash
docker compose up -d --build api
```

查看容器资源：

```bash
docker stats
```

进入 API 容器：

```bash
docker compose exec api /bin/bash
```

---

## 7. 故障排查

### 7.1 API 启动失败

- 看日志：`docker compose logs -f api`
- 检查 `.env` 是否有误（尤其 `DATABASE_URL`）

### 7.2 文档一直 pending

- 检查 API 日志：`docker compose logs -f api`
- 检查 DB 是否正常启动

### 7.3 Chat 返回无依据

- 检查文档是否 `ready`
- 检查 `QWEN_API_KEY` 是否有效
- 检查模型名是否可用

---

## 8. 生产建议

- 使用外部托管 PostgreSQL
- 使用对象存储（OSS/S3）替代本地文件
- 引入反向代理 + TLS + WAF
- 增加监控告警（Prometheus/Grafana）
- 对敏感信息使用密钥管理系统，不落仓库
