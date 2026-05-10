# 学科知识整合智能体

AI 全栈黑客松项目：多教材知识整合系统，支持知识图谱构建、跨教材去重提纯、RAG 精准问答。

## 技术栈

- **前端**: React + Vite + Ant Design + ECharts
- **后端**: FastAPI + Python
- **向量库**: ChromaDB / FAISS
- **Embedding**: sentence-transformers (BGE-small-zh)

## 环境要求

- Python >= 3.10
- Node.js >= 18

## 快速启动

### 方式一：Docker（推荐）

```bash
# 确保已配置 backend/.env
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入 OPENAI_API_KEY

# 一键启动前后端
docker-compose up --build

# 打开浏览器访问 http://localhost:5173
```

### 方式二：本地开发

#### 1. 启动后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY 或本地 LLM 配置

# 启动服务
uvicorn app.main:app --reload --port 8000
```

#### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

打开浏览器访问 http://localhost:5173

## 项目结构

```
.
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── models/            # Pydantic 数据模型
│   │   ├── routers/           # API 路由
│   │   ├── services/          # 业务逻辑
│   │   └── utils/             # LLM / Embedding 工具
│   ├── data/                  # 上传文件、向量库、图谱数据
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # 主布局
│   │   ├── api/               # API 客户端
│   │   └── components/        # UI 组件
│   ├── package.json
│   └── vite.config.js
├── docs/                      # 设计文档
├── report/                    # 整合报告输出
└── README.md
```

## 功能模块

1. **教材上传与解析**：支持 PDF/Markdown/TXT，逐页解析章节结构
2. **知识图谱构建**：逐章调用 LLM 提取知识点与关系，ECharts 力导向图可视化
3. **跨教材整合**：Embedding 相似度 + LLM 精判，自动去重提纯，压缩比 ≤ 30%
4. **RAG 精准问答**：分块 → Embedding → 向量检索 → LLM 生成带引用回答
5. **多轮对话**：教师可询问整合原因、修改整合决策
6. **整合报告**：自动生成 Markdown 格式整合报告

## 文档清单

- `docs/需求分析.md`
- `docs/系统设计.md`
- `docs/Agent 架构说明.md`
- `report/整合报告.md`
