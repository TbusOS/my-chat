"""
MCP Server - macOS AI 训练桥接服务

将 macOS 上的模型训练、推理、系统监控能力封装为 HTTP API，
供 Docker 中的 LobeChat / Agent 通过 MCP 协议调用。

运行环境：macOS 原生（不要放 Docker 里，需要访问 GPU）
启动命令：uvicorn mcp_server:app --host 0.0.0.0 --port 8811
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import subprocess
import psutil

app = FastAPI(
    title="AI Training MCP Server",
    description="Bridge between Docker services and macOS native AI capabilities",
    version="1.0.0",
)


# === 请求/响应模型 ===


class TrainRequest(BaseModel):
    model: str = Field(
        description="MLX model identifier",
        examples=["mlx-community/Qwen2.5-7B-Instruct-4bit"],
    )
    data_path: str = Field(description="Path to training dataset")
    adapter_path: str = Field(description="Output path for LoRA adapter")
    batch_size: int = Field(default=4, ge=1, le=32)
    num_iters: int = Field(default=1000, ge=1, le=100000)
    learning_rate: float = Field(default=1e-5, gt=0, lt=1)


class TrainResponse(BaseModel):
    status: str
    pid: int
    message: str


class JobStatus(BaseModel):
    pid: int
    status: str
    model: str
    exit_code: int | None = None


class SystemInfo(BaseModel):
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    cpu_percent: float


class ModelInfo(BaseModel):
    name: str
    size: str


# === 训练任务管理 ===

active_jobs: dict[int, dict] = {}


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
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=500,
            detail=f"mlx_lm not found. Install with: pip install mlx-lm. Error: {err}",
        )

    active_jobs[proc.pid] = {
        "model": req.model,
        "status": "running",
        "process": proc,
    }

    return TrainResponse(
        status="started",
        pid=proc.pid,
        message=f"Training started: {req.model} → {req.adapter_path}",
    )


@app.get("/tools/check_status/{pid}", response_model=JobStatus)
async def check_status(pid: int):
    """查询训练任务状态"""
    job = active_jobs.get(pid)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {pid} not found")

    poll_result = job["process"].poll()

    if poll_result is None:
        return JobStatus(pid=pid, status="running", model=job["model"])

    status = "completed" if poll_result == 0 else "failed"
    active_jobs[pid]["status"] = status

    return JobStatus(
        pid=pid,
        status=status,
        exit_code=poll_result,
        model=job["model"],
    )


@app.get("/tools/list_jobs")
async def list_jobs():
    """列出所有训练任务"""
    jobs = []
    for pid, job in active_jobs.items():
        poll_result = job["process"].poll()
        status = "running" if poll_result is None else (
            "completed" if poll_result == 0 else "failed"
        )
        jobs.append({
            "pid": pid,
            "model": job["model"],
            "status": status,
        })
    return {"jobs": jobs}


@app.post("/tools/stop_job/{pid}")
async def stop_job(pid: int):
    """停止训练任务"""
    job = active_jobs.get(pid)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {pid} not found")

    job["process"].terminate()
    active_jobs[pid]["status"] = "stopped"
    return {"pid": pid, "status": "stopped"}


# === 模型管理 ===


@app.get("/tools/list_models")
async def list_models():
    """列出 Ollama 已下载的模型"""
    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {result.stderr}",
        )

    lines = result.stdout.strip().split("\n")
    models: list[ModelInfo] = []

    for line in lines[1:]:
        parts = line.split()
        if parts:
            models.append(ModelInfo(
                name=parts[0],
                size=parts[2] if len(parts) > 2 else "unknown",
            ))

    return {"models": models}


# === 系统监控 ===


@app.get("/tools/system_info", response_model=SystemInfo)
async def system_info():
    """查询系统资源使用情况"""
    memory = psutil.virtual_memory()
    return SystemInfo(
        memory_total_gb=round(memory.total / (1024**3), 1),
        memory_used_gb=round(memory.used / (1024**3), 1),
        memory_percent=memory.percent,
        cpu_percent=psutil.cpu_percent(interval=1),
    )


# === 健康检查 ===


@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "ok", "service": "mcp-server"}
