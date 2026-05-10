import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import upload, parse, graph, merge, rag, chat, report
from app.services.storage import StorageService

# 确保数据目录存在
os.makedirs("data/uploaded", exist_ok=True)
os.makedirs("data/graphs", exist_ok=True)
os.makedirs("data/vectors", exist_ok=True)
os.makedirs("data/reports", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时加载已有数据
    StorageService.load_all()
    yield
    # 关闭时持久化数据
    StorageService.save_all()


app = FastAPI(
    title="学科知识整合智能体 API",
    description="AI 全栈黑客松 - 多教材知识整合",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(upload.router, prefix="/api/upload", tags=["上传"])
app.include_router(parse.router, prefix="/api/parse", tags=["解析"])
app.include_router(graph.router, prefix="/api/graph", tags=["知识图谱"])
app.include_router(merge.router, prefix="/api/merge", tags=["跨教材整合"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG 问答"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
app.include_router(report.router, prefix="/api/report", tags=["报告"])

# 如果存在前端构建产物，挂载静态文件
if os.path.exists("../frontend/dist"):
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}
