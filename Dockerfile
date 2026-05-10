# 构建阶段：前端
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# 运行阶段：Python 后端 + 静态文件服务
FROM python:3.12-slim
WORKDIR /app

# 安装编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/
WORKDIR /app/backend

# 复制前端构建产物到 backend/dist，让 FastAPI 挂载
COPY --from=frontend-builder /app/frontend/dist ./dist

# 确保数据目录存在
RUN mkdir -p data/uploaded data/graphs data/vectors data/reports

EXPOSE 7860

# 魔搭创空间默认暴露 7860 端口
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
