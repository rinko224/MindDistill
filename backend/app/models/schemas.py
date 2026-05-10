from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ================== 教材相关 ==================

class Chapter(BaseModel):
    chapter_id: str
    title: str
    page_start: int
    page_end: int
    content: str
    char_count: int


class Textbook(BaseModel):
    textbook_id: str
    filename: str
    title: str
    total_pages: int
    total_chars: int
    format: str
    status: Literal["parsing", "completed", "failed"] = "parsing"
    graph_status: Literal["none", "building", "completed", "failed"] = "none"
    chapters: List[Chapter] = []


class TextbookListResponse(BaseModel):
    books: List[Textbook]
    total: int


# ================== 知识图谱相关 ==================

class KnowledgeNode(BaseModel):
    id: str
    name: str
    definition: str
    category: str
    chapter: str
    page: int
    textbook_id: str


class KnowledgeEdge(BaseModel):
    source: str
    target: str
    relation_type: Literal["prerequisite", "parallel", "contains", "applies_to"]
    description: str


class GraphData(BaseModel):
    nodes: List[KnowledgeNode]
    edges: List[KnowledgeEdge]


# ================== 整合相关 ==================

class MergeDecision(BaseModel):
    decision_id: str
    action: Literal["merge", "keep", "remove"]
    affected_nodes: List[str]
    result_node: Optional[str] = None
    reason: str
    confidence: float


class MergeResult(BaseModel):
    decisions: List[MergeDecision]
    original_chars: int
    merged_chars: int
    ratio: float
    original_nodes: int
    merged_nodes: int


# ================== RAG 相关 ==================

class RAGQueryRequest(BaseModel):
    question: str
    top_k: int = 5


class Citation(BaseModel):
    textbook: str
    chapter: str
    page: int
    relevance_score: float


class RAGQueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    source_chunks: List[str]


class RAGStatus(BaseModel):
    indexed_books: int
    total_chunks: int
    is_ready: bool


# ================== 对话相关 ==================

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str
    updated_graph: Optional[GraphData] = None
    updated_merge: Optional[MergeResult] = None


# ================== 报告相关 ==================

class ReportData(BaseModel):
    overview: dict
    decisions_summary: dict
    graph_stats: dict
    cases: List[dict]
    completeness: str
