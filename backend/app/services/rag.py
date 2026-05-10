import json
import os
from typing import List, Dict, Tuple
import chromadb
from chromadb.config import Settings

from app.models.schemas import RAGQueryResponse, Citation
from app.services.storage import StorageService
from app.utils.embedding import EmbeddingService
from app.utils.llm import LLMClient


class RAGService:
    """RAG（检索增强生成）服务，支持精准问答"""
    
    index_ready = False
    indexed_books = 0
    total_chunks = 0
    
    # ChromaDB 客户端和集合
    _client = None
    _collection = None
    _chunk_metadata = {}  # 保存chunk的元数据：chunk_id -> {textbook, chapter, page, content}
    
    CHUNK_SIZE = 700  # 每个chunk约700字
    OVERLAP_SIZE = 75  # 相邻chunk重叠75字

    @classmethod
    def _get_client(cls):
        """获取或创建ChromaDB客户端"""
        if cls._client is None:
            db_path = "data/vectors"
            os.makedirs(db_path, exist_ok=True)
            settings = Settings(
                anonymized_telemetry=False,
            )
            cls._client = chromadb.PersistentClient(path=db_path, settings=settings)
        return cls._client

    @classmethod
    def _get_collection(cls):
        """获取或创建ChromaDB集合"""
        if cls._collection is None:
            client = cls._get_client()
            cls._collection = client.get_or_create_collection(
                name="textbook_chunks",
                metadata={"hnsw:space": "cosine"}
            )
        return cls._collection

    @classmethod
    def _split_into_chunks(cls, content: str, metadata: dict) -> List[Dict]:
        """
        将文本分块，支持重叠
        
        Args:
            content: 文本内容
            metadata: 元数据 {textbook_id, textbook_name, chapter_id, chapter_title, page_start, page_end}
            
        Returns:
            chunks列表，每个chunk包含：
            {
                "id": "chunk_xxx",
                "content": "chunk文本",
                "metadata": {...}
            }
        """
        chunks = []
        content_len = len(content)
        chunk_id_prefix = f"{metadata['textbook_id']}_{metadata['chapter_id']}"
        chunk_index = 0
        
        i = 0
        while i < content_len:
            # 提取chunk
            chunk_end = min(i + cls.CHUNK_SIZE, content_len)
            chunk_text = content[i:chunk_end]
            
            # 如果不是最后一个chunk，尽量在句号或空格处分割
            if chunk_end < content_len:
                # 从chunk_text末尾往回找最近的句号或换行
                for j in range(len(chunk_text) - 1, max(len(chunk_text) - 100, -1), -1):
                    if chunk_text[j] in ('。', '！', '？', '\n', ' '):
                        chunk_text = chunk_text[:j + 1]
                        chunk_end = i + j + 1
                        break
            
            if len(chunk_text.strip()) > 50:  # 至少50字
                chunk_id = f"{chunk_id_prefix}_{chunk_index}"
                chunks.append({
                    "id": chunk_id,
                    "content": chunk_text.strip(),
                    "metadata": {
                        "textbook_id": metadata['textbook_id'],
                        "textbook_name": metadata['textbook_name'],
                        "chapter_id": metadata['chapter_id'],
                        "chapter_title": metadata['chapter_title'],
                        "page_start": metadata['page_start'],
                        "page_end": metadata['page_end'],
                        "char_count": len(chunk_text)
                    }
                })
                chunk_index += 1
            
            if chunk_end >= content_len:
                break
                
            # 移动到下一个chunk（考虑重叠）
            i = chunk_end - cls.OVERLAP_SIZE
            if i >= chunk_end:
                break
        
        return chunks

    @classmethod
    async def index_all(cls):
        """
        对所有已解析的教材建立向量索引
        
        处理流程：
        1. 遍历所有教材的章节
        2. 对每个章节进行分块（500-800字，50-100字重叠）
        3. 计算每个chunk的embedding
        4. 存入ChromaDB
        """
        try:
            collection = cls._get_collection()
            cls._chunk_metadata = {}
            
            total_chunks_added = 0
            
            # 遍历所有教材
            for textbook_id, textbook in StorageService.books.items():
                # 遍历每个章节
                for chapter in textbook.chapters:
                    # 分块
                    chunks = cls._split_into_chunks(
                        chapter.content,
                        {
                            "textbook_id": textbook_id,
                            "textbook_name": textbook.title,
                            "chapter_id": chapter.chapter_id,
                            "chapter_title": chapter.title,
                            "page_start": chapter.page_start,
                            "page_end": chapter.page_end,
                        }
                    )
                    
                    if not chunks:
                        continue
                    
                    # 获取embedding
                    chunk_texts = [c["content"] for c in chunks]
                    embeddings = EmbeddingService.encode(chunk_texts)
                    
                    # 添加到ChromaDB
                    ids = [c["id"] for c in chunks]
                    metadatas = [c["metadata"] for c in chunks]
                    documents = chunk_texts
                    
                    collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        documents=documents,
                    )
                    
                    # 保存chunk元数据
                    for chunk in chunks:
                        cls._chunk_metadata[chunk["id"]] = {
                            "content": chunk["content"],
                            **chunk["metadata"]
                        }
                    
                    total_chunks_added += len(chunks)
            
            cls.index_ready = True
            cls.indexed_books = len(StorageService.books)
            cls.total_chunks = total_chunks_added
            
            return {
                "message": f"索引建立完成：{cls.indexed_books} 本教材，{total_chunks_added} 个知识块",
                "indexed_books": cls.indexed_books,
                "total_chunks": total_chunks_added,
            }
        except Exception as e:
            print(f"Error indexing books: {e}")
            import traceback
            traceback.print_exc()
            return {
                "message": f"索引建立失败: {str(e)}",
                "error": str(e)
            }

    @classmethod
    async def query(cls, question: str, top_k: int = 5) -> RAGQueryResponse:
        """
        执行RAG查询
        
        流程：
        1. 问题embedding
        2. 向量检索top_k chunks
        3. 组装上下文prompt
        4. 调用LLM生成回答
        5. 返回回答和引用
        """
        if not cls.index_ready:
            return RAGQueryResponse(
                answer="索引尚未建立，请先执行索引操作。",
                citations=[],
                source_chunks=[],
            )

        try:
            # 1. 问题embedding
            question_embedding = EmbeddingService.encode([question])[0]
            
            # 2. 向量检索
            collection = cls._get_collection()
            results = collection.query(
                query_embeddings=[question_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results or not results["documents"] or len(results["documents"]) == 0 or len(results["documents"][0]) == 0:
                return RAGQueryResponse(
                    answer="知识库中未找到相关信息，请尝试其他问法。",
                    citations=[],
                    source_chunks=[],
                )
            
            # 提取检索结果
            retrieved_docs = results["documents"][0]  # batch中第一个query的结果
            retrieved_metadatas = results["metadatas"][0]
            retrieved_distances = results["distances"][0]  # 距离（越小相似度越高）
            
            # 将距离转换为相似度分数（0-1之间）
            relevance_scores = [1 - min(d, 1.0) for d in retrieved_distances]
            
            # 3. 构建上下文
            context_parts = []
            citations = []
            source_chunks = []
            
            seen_textbooks = set()
            for i, (doc, metadata, score) in enumerate(zip(retrieved_docs, retrieved_metadatas, relevance_scores)):
                context_parts.append(f"【{metadata['textbook_name']} - {metadata['chapter_title']} 第{metadata['page_start']}页】\n{doc}")
                source_chunks.append(doc)
                
                # 每本教材只添加一个引用（避免重复）
                textbook_key = f"{metadata['textbook_name']}_{metadata['chapter_id']}"
                if textbook_key not in seen_textbooks:
                    citations.append(Citation(
                        textbook=metadata['textbook_name'],
                        chapter=metadata['chapter_title'],
                        page=metadata['page_start'],
                        relevance_score=round(score, 3)
                    ))
                    seen_textbooks.add(textbook_key)
            
            context_text = "\n\n".join(context_parts)
            
            # 4. 构建prompt并调用LLM
            system_prompt = """你是一个精准的教材问答助手。你的任务是：
1. 只基于提供的教材内容回答问题
2. 确保每个回答都有来源依据
3. 如果教材中找不到相关信息，明确说明"当前知识库中未找到相关信息"
4. 回答要准确、简洁、通俗易懂"""
            
            user_prompt = f"""用户问题：{question}

相关教材内容：
{context_text}

请基于上述教材内容回答用户问题。如果内容不足以回答，请明确说明。"""
            
            answer = await LLMClient.ask(user_prompt, system=system_prompt, temperature=0.3)
            
            return RAGQueryResponse(
                answer=answer,
                citations=citations,
                source_chunks=source_chunks,
            )
            
        except Exception as e:
            print(f"Error querying RAG: {e}")
            import traceback
            traceback.print_exc()
            return RAGQueryResponse(
                answer=f"查询过程中出现错误: {str(e)}",
                citations=[],
                source_chunks=[],
            )

    @classmethod
    def get_status(cls):
        """获取RAG索引状态"""
        return {
            "indexed_books": cls.indexed_books,
            "total_chunks": cls.total_chunks,
            "is_ready": cls.index_ready,
        }
    
    @classmethod
    def reset_index(cls):
        """重置索引（用于重新构建）"""
        try:
            if cls._client is not None:
                try:
                    cls._client.delete_collection(name="textbook_chunks")
                except ValueError:
                    pass
                cls._collection = None
            cls.index_ready = False
            cls.indexed_books = 0
            cls.total_chunks = 0
            cls._chunk_metadata = {}
            return {"message": "索引已重置"}
        except Exception as e:
            return {"message": f"重置索引失败: {str(e)}", "error": str(e)}

    @classmethod
    def delete_book(cls, book_id: str):
        """删除指定教材的向量索引"""
        try:
            if cls._client is not None:
                collection = cls._get_collection()
                collection.delete(where={"textbook_id": book_id})
                
                # Update chunk metadata in memory if needed
                keys_to_delete = [k for k, v in cls._chunk_metadata.items() if v.get("textbook_id") == book_id]
                for k in keys_to_delete:
                    del cls._chunk_metadata[k]
                    
            return {"success": True}
        except Exception as e:
            print(f"Error deleting book from RAG: {e}")
            return {"success": False, "error": str(e)}
