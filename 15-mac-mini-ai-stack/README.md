# Mac Mini 本地 AI 全栈部署方案

> macOS 原生跑模型 + Docker 跑服务，一台 Mac Mini 搞定训练、推理、Agent 开发全流程

## 为什么选 Mac Mini

- Apple Silicon 统一内存架构，GPU/CPU 共享内存，大模型推理性价比极高
- Metal / MLX 原生加速，7B～70B 模型均可本地运行
- 功耗低、无噪音，适合 24/7 运行
- 容器化运行时支持完善（Docker Desktop 或 Colima）

## 硬件选购建议

| 配置 | 内存 | 适合场景 | 推荐度 |
|------|------|---------|--------|
| M4 | 24GB | 7B 推理，轻量开发 | 入门 |
| M4 Pro | 36GB | 7B 训练 + 13B 推理 + 多服务并发 | **推荐** |
| M4 Pro/Max | 64GB | 70B 量化推理，多模型并行，不操心内存 | 一步到位 |

> **关键提醒**：Apple Silicon 内存焊死，无法后期升级。预算允许尽量选大内存。

---

## 核心架构

### 设计原则

**需要 GPU 的留 macOS 原生，其他全部容器化。**

- macOS 原生：模型训练、推理（需要 Metal/MLX 加速）
- Docker：前端界面、Bot 服务、数据库、未来新 Agent

### 架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                        Mac Mini (Apple Silicon)                  │
│                                                                  │
│  ┌─────────────────────────────────┐  ┌───────────────────────┐  │
│  │       macOS 原生 (GPU 独占)      │  │  Docker / Colima      │  │
│  │                                 │  │                       │  │
│  │  ┌───────────┐ ┌─────────────┐  │  │  ┌───────────────┐   │  │
│  │  │  Ollama    │ │  MLX        │  │  │  │   LobeChat    │   │  │
│  │  │  模型推理   │ │  模型训练    │  │  │  │   :3210       │   │  │
│  │  │  :11434    │ │  /微调      │  │  │  └───────┬───────┘   │  │
│  │  └─────┬─────┘ └──────┬──────┘  │  │          │           │  │
│  │        │              │         │  │  ┌───────────────┐   │  │
│  │  ┌─────┴──────────────┴──────┐  │  │  │  飞书 Bot     │   │  │
│  │  │      MCP Server           │  │  │  │  :9000        │   │  │
│  │  │      :8811                │◄─┼──┼──┤               │   │  │
│  │  │  · train_model()         │  │  │  └───────────────┘   │  │
│  │  │  · list_models()         │  │  │                       │  │
│  │  │  · check_status()        │  │  │  ┌───────────────┐   │  │
│  │  │  · check_gpu_usage()     │  │  │  │  PostgreSQL    │   │  │
│  │  └──────────────────────────┘  │  │  │  :5432         │   │  │
│  │                                 │  │  └───────────────┘   │  │
│  │  ┌──────────────────────────┐  │  │                       │  │
│  │  │  开发工具                  │  │  │  ┌───────────────┐   │  │
│  │  │  VS Code / Cursor        │  │  │  │  Redis         │   │  │
│  │  │  Claude Code             │  │  │  │  :6379         │   │  │
│  │  └──────────────────────────┘  │  │  └───────────────┘   │  │
│  └─────────────────────────────────┘  └───────────────────────┘  │
│                                                                  │
│        host.docker.internal / HOST_IP ← 容器访问宿主机            │
└──────────────────────────────────────────────────────────────────┘
```

### 数据流

```
用户聊天请求
    │
    ▼
┌──────────┐   HTTP API    ┌──────────┐   Metal/MLX   ┌──────────┐
│ LobeChat │ ────────────→ │  Ollama  │ ───────────→  │   GPU    │
│ (Docker) │   :11434      │ (macOS)  │               │ 推理加速  │
└──────────┘               └──────────┘               └──────────┘

用户发起训练
    │
    ▼
┌──────────┐   MCP call    ┌──────────┐   MLX        ┌──────────┐
│ LobeChat │ ────────────→ │   MCP    │ ───────────→ │  模型训练  │
│ (Docker) │   :8811       │  Server  │              │  LoRA/QLoRA│
└──────────┘               │ (macOS)  │              └──────────┘
                           └──────────┘
```

---

## 快速开始

### 前置条件

- macOS 14+ (Sonoma 或更新)
- 容器运行时：[Docker Desktop](#方案-a-docker-desktop) 或 [Colima](#方案-b-colima推荐)（二选一）
- [Homebrew](https://brew.sh/)

### Step 1：安装 macOS 原生服务

```bash
# 安装 Ollama
brew install ollama

# 启动 Ollama 服务（绑定所有接口，让 Docker 能访问）
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# 拉取模型
ollama pull qwen2.5:7b
ollama pull llama3.1:8b

# （可选）安装 MLX 用于训练
pip install mlx-lm
```

### Step 2：启动 Docker 服务

```bash
cd 15-mac-mini-ai-stack

# 复制环境变量模板
cp .env.example .env
# 编辑 .env 填入你的配置
vim .env

# 一键启动所有服务
docker compose up -d

# 查看运行状态
docker compose ps
```

### Step 3：访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| LobeChat | http://localhost:3210 | 聊天界面 |
| Ollama API | http://localhost:11434 | 模型推理 API |
| MCP Server | http://localhost:8811 | 训练控制 API |

---

## Docker Compose 配置详解

完整配置见 [docker-compose.yml](./docker-compose.yml)。

### 服务清单

| 服务 | 镜像 | 端口 | 用途 |
|------|------|------|------|
| lobechat | lobehub/lobe-chat | 3210 | 聊天前端 |
| postgres | postgres:16 | 5432 | 数据存储 |
| redis | redis:7-alpine | 6379 | 缓存/会话 |

### Volume 挂载策略

```
代码 → bind mount（挂载到宿主机目录，方便编辑）
数据 → named volume（Docker 管理，持久化）
配置 → bind mount（版本控制）
```

数据不会因为容器删除而丢失。只有显式执行 `docker volume rm` 才会删除数据。

---

## MCP Server：打通 Docker ↔ macOS

MCP（Model Context Protocol）让 Docker 中的 LobeChat 可以调用 macOS 上的能力。

### 为什么需要 MCP Server

Docker 容器无法直接访问宿主机的 GPU 和文件系统。MCP Server 作为桥梁，将 macOS 上的训练、推理、系统监控等能力封装为标准化的工具接口。

### 架构

```
LobeChat (Docker)
    │
    │  调用 MCP 工具
    ▼
MCP Server (macOS :8811)
    │
    ├── train_model()        → 调用 MLX 启动 LoRA 微调
    ├── list_models()        → 列出已下载的模型
    ├── check_status(pid)    → 查询训练进度
    ├── check_gpu_usage()    → 读取 GPU/内存使用率
    ├── run_inference()      → 直接调用 MLX 推理
    └── list_datasets()      → 列出可用数据集
```

### 示例：MCP Server 实现

```python
"""
MCP Server - 将 macOS 训练能力暴露给 Docker 中的服务。
运行在 macOS 原生环境（非 Docker），需要访问 GPU。
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import psutil

app = FastAPI(title="AI Training MCP Server")


class TrainRequest(BaseModel):
    model: str           # e.g. "mlx-community/Qwen2.5-7B-Instruct-4bit"
    data_path: str       # 训练数据路径
    adapter_path: str    # LoRA adapter 输出路径
    batch_size: int = 4
    num_iters: int = 1000
    learning_rate: float = 1e-5


class TrainResponse(BaseModel):
    status: str
    pid: int
    message: str


# 训练任务跟踪
active_jobs: dict = {}


@app.post("/tools/train_model", response_model=TrainResponse)
async def train_model(req: TrainRequest):
    """启动 MLX LoRA 微调任务"""
    cmd = [
        "mlx_lm.lora",
        "--model", req.model,
        "--data", req.data_path,
        "--adapter-path", req.adapter_path,
        "--batch-size", str(req.batch_size),
        "--num-iters", str(req.num_iters),
        "--learning-rate", str(req.learning_rate),
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        active_jobs[proc.pid] = {
            "model": req.model,
            "status": "running",
            "process": proc,
        }
        return TrainResponse(
            status="started",
            pid=proc.pid,
            message=f"Training started: {req.model}",
        )
    except FileNotFoundError as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.get("/tools/check_status/{pid}")
async def check_status(pid: int):
    """查询训练任务状态"""
    job = active_jobs.get(pid)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    poll_result = job["process"].poll()
    if poll_result is None:
        return {"pid": pid, "status": "running", "model": job["model"]}

    return {
        "pid": pid,
        "status": "completed" if poll_result == 0 else "failed",
        "exit_code": poll_result,
        "model": job["model"],
    }


@app.get("/tools/list_models")
async def list_models():
    """列出 Ollama 已下载的模型"""
    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True,
    )
    lines = result.stdout.strip().split("\n")
    models = []
    for line in lines[1:]:  # 跳过表头
        parts = line.split()
        if parts:
            models.append({
                "name": parts[0],
                "size": parts[2] if len(parts) > 2 else "unknown",
            })
    return {"models": models}


@app.get("/tools/check_gpu_usage")
async def check_gpu_usage():
    """查询系统资源使用情况"""
    memory = psutil.virtual_memory()
    return {
        "memory_total_gb": round(memory.total / (1024**3), 1),
        "memory_used_gb": round(memory.used / (1024**3), 1),
        "memory_percent": memory.percent,
        "cpu_percent": psutil.cpu_percent(interval=1),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 启动 MCP Server

```bash
# 安装依赖
pip install fastapi uvicorn psutil

# 启动（macOS 原生运行，不要放 Docker 里）
uvicorn mcp_server:app --host 0.0.0.0 --port 8811
```

---

## 文件结构

```
15-mac-mini-ai-stack/
├── README.md                  # 本文档
├── docker-compose.yml         # Docker 服务编排
├── .env.example               # 环境变量模板
├── mcp-server/
│   ├── mcp_server.py          # MCP Server 实现
│   └── requirements.txt       # Python 依赖
└── scripts/
    ├── setup.sh               # 一键安装脚本
    └── start-all.sh           # 一键启动脚本
```

---

## macOS 文件目录规划

```
~/
├── projects/              # 开发代码（bind mount 到 Docker）
│   ├── lobechat-config/   # LobeChat 自定义配置
│   └── my-agents/         # 自定义 Agent 代码
├── docker/
│   ├── docker-compose.yml # 服务编排
│   └── .env               # 密钥（不要提交 git）
├── models/                # 模型文件
│   ├── ollama/            # Ollama 模型（默认 ~/.ollama）
│   └── mlx/               # MLX 格式模型
├── datasets/              # 训练数据集
└── adapters/              # LoRA adapter 输出
```

---

## 扩展：添加新服务

Docker 架构的优势是扩展简单。添加新 Agent 只需在 `docker-compose.yml` 中加一个 service：

```yaml
services:
  # ... 已有服务 ...

  my-new-agent:
    build: ../projects/my-agents/new-agent
    ports:
      - "8090:8090"
    environment:
      - OLLAMA_URL=http://host.docker.internal:11434
    restart: unless-stopped
```

然后：

```bash
docker compose up -d my-new-agent
```

---

## 常用命令速查

```bash
# === Docker 管理 ===
docker compose up -d            # 启动所有服务
docker compose down             # 停止所有服务
docker compose ps               # 查看运行状态
docker compose logs -f lobechat # 查看某个服务日志
docker compose restart lobechat # 重启某个服务
docker compose up -d --build    # 重建并启动（代码更新后）

# === Ollama 模型管理 ===
ollama list                     # 列出已下载模型
ollama pull <model>             # 下载模型
ollama rm <model>               # 删除模型
ollama show <model>             # 查看模型信息

# === MLX 训练 ===
mlx_lm.lora \
  --model mlx-community/Qwen2.5-7B-Instruct-4bit \
  --data ./datasets/my-data \
  --adapter-path ./adapters/my-lora \
  --batch-size 4 \
  --num-iters 1000

# === 系统监控 ===
top -l 1 | head -n 10           # CPU/内存概览
sudo powermetrics --samplers gpu_power -n 1  # GPU 功耗
```

---

## 容器运行时：Docker Desktop vs Colima

本方案支持两种容器运行时，docker-compose.yml 无需修改，两个都兼容。

### 对比

| | Docker Desktop | Colima |
|---|---|---|
| 价格 | 个人免费，公司 >250 人需付费 | 完全免费开源 |
| 内存占用 | 较重，后台常驻 ~1-2GB | 更轻量，按需启停 |
| `host.docker.internal` | 开箱即用 | 需 `--network-address` 参数 |
| GUI | 有图形管理界面 | 纯命令行 |
| docker compose | 内置 | 需额外安装 `docker-compose` |
| 文件挂载性能 | 较好（VirtioFS） | 稍慢（sshfs/9p） |
| macOS 大版本升级 | 通常平滑 | 偶尔需重建 VM |

### 方案 A: Docker Desktop

最简单，开箱即用：

```bash
# 安装
brew install --cask docker

# 启动：打开 Docker Desktop 应用即可
# host.docker.internal 自动可用，无需额外配置
```

### 方案 B: Colima（推荐）

更轻量，省内存留给模型训练：

```bash
# 安装
brew install colima docker docker-compose

# 启动（按实际内存调整参数）
colima start \
  --cpu 4 \
  --memory 8 \
  --disk 60 \
  --network-address

# 验证
docker ps
docker compose version
```

#### Colima 访问宿主机

Colima 不自带 `host.docker.internal`，需要用宿主机 IP：

```bash
# 查看 Colima 分配的网络地址
colima ls
# NAME     RUNTIME  STATUS   ADDRESS         ARCH     CPUS  MEMORY  DISK
# default  docker   Running  192.168.106.2   aarch64  4     8GiB    60GiB
```

在 `.env` 中配置宿主机 IP：

```bash
# .env
# Colima 用户：填入宿主机网关 IP（通常是 .1）
HOST_IP=192.168.106.1

# Docker Desktop 用户：保持默认即可
# HOST_IP=host.docker.internal
```

docker-compose.yml 已兼容两种方式，通过 `HOST_IP` 环境变量切换。

#### Colima 常用命令

```bash
colima start              # 启动
colima stop               # 停止（释放所有内存）
colima delete             # 删除 VM（volume 数据不受影响）
colima status             # 查看状态
colima ssh                # 进入 Colima VM（调试用）
```

#### Colima 已知问题及解决

**1. 重启后 Docker socket 断连**

```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

解决：`colima start` 重新启动。或设置开机自启：

```bash
brew services start colima
```

**2. 文件挂载性能偏慢**

Colima 底层用 sshfs/9p 挂载宿主机目录，对频繁读写（如 Node.js 热更新）有感知。
本方案中数据库、Redis 均使用 named volume，不受影响。

**3. macOS 大版本升级后不兼容**

系统升级（如 Sonoma → Sequoia）后 Colima 底层的 Lima VM 偶尔异常。

解决：

```bash
colima delete && colima start --cpu 4 --memory 8 --disk 60 --network-address
```

named volume 中的数据不受影响。

### 推荐选择

- **省心** → Docker Desktop（GUI 管理，开箱即用）
- **省内存** → Colima（轻量，按需启停，内存留给模型训练）

---

## 常见问题

### Q: Docker 容器怎么访问 macOS 上的 Ollama？

**Docker Desktop**：使用 `host.docker.internal`，开箱即用：

```
http://host.docker.internal:11434
```

**Colima**：在 `.env` 中设置 `HOST_IP` 为宿主机 IP（通过 `colima ls` 查看），docker-compose.yml 会自动使用。

### Q: 虚拟机和 Docker 该选哪个？

**选 Docker**。虚拟机会固定分配内存（如 8GB 给 Ubuntu），macOS 训练模型时拿不回来。Docker 共享内存，用多少占多少，更灵活。

### Q: 训练模型时 Docker 服务会卡吗？

Apple Silicon 统一内存，训练会占用大量内存和 GPU。建议：
- 训练时关闭不必要的 Docker 服务：`docker compose stop lobechat`
- Docker Desktop 用户：限制内存上限（Settings → Resources）
- Colima 用户：启动时指定内存上限（`--memory 8`），不训练时可分配更多
- 36GB+ 内存基本不用担心

### Q: 数据会不会因为容器删除而丢失？

不会。使用 named volume 的数据独立于容器生命周期。只有显式执行 `docker volume rm` 才会删除。代码通过 bind mount 挂载，始终保存在宿主机上。

### Q: 如何备份整个环境？

```bash
# 备份配置
cp -r ~/docker ~/docker-backup

# 备份数据库
docker compose exec postgres pg_dump -U postgres > backup.sql

# 备份模型（体积大，按需备份）
# Ollama 模型默认在 ~/.ollama/models/
```

---

## License

MIT
