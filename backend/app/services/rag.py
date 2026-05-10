from typing import List

from app.models.schemas import RAGQueryResponse, Citation
from app.services.storage import StorageService
from app.utils.embedding import EmbeddingService
from app.utils.llm import LLMClient


class RAGService:
    index_ready = False
    indexed_books = 0
    total_chunks = 0

    @classmethod
    async def index_all(cls):
        # TODO:
        # 1. 将所有教材章节按 500-800 字分块，50-100 字重叠
        # 2. 计算每个 chunk 的 embedding
        # 3. 存入向量数据库（ChromaDB 或 FAISS）
        cls.index_ready = True
        cls.indexed_books = len(StorageService.books)
        return {"message": "Indexing completed"}

    @classmethod
    async def query(cls, question: str, top_k: int = 5) -> RAGQueryResponse:
        if not cls.index_ready:
            return RAGQueryResponse(
                answer="索引尚未建立，请先执行索引操作。",
                citations=[],
                source_chunks=[],
            )

        # TODO:
        # 1. 问题 embedding
        # 2. 向量检索 top_k chunks
        # 3. 组装 Prompt（含上下文和引用约束）
        # 4. 调用 LLM 生成回答

        return RAGQueryResponse(
            answer="TODO: 生成回答",
            citations=[],
            source_chunks=[],
        )

    @classmethod
    def get_status(cls):
        return {
            "indexed_books": cls.indexed_books,
            "total_chunks": cls.total_chunks,
            "is_ready": cls.index_ready,
        }
