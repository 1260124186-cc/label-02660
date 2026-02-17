"""
比赛证书自动识别管理系统 - 后端入口
FastAPI 应用
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.utils.logger import setup_logging
from src.api.cert_api import router as cert_router
from src.api.template_api import router as template_router

setup_logging(log_dir=os.path.join(PROJECT_ROOT, "logs"))

app = FastAPI(
    title="比赛证书自动识别管理系统",
    description="基于 PaddleOCR 的证书识别与信息提取 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件：输出目录
os.makedirs(os.path.join(PROJECT_ROOT, "output"), exist_ok=True)
app.mount("/output", StaticFiles(directory=os.path.join(PROJECT_ROOT, "output")), name="output")

app.include_router(cert_router, prefix="/api/cert", tags=["证书识别"])
app.include_router(template_router, prefix="/api/template", tags=["模板管理"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "cert-ocr-backend"}
