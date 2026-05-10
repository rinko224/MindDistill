from fastapi import APIRouter

from app.models.schemas import RAGQueryRequest, RAGQueryResponse, RAGStatus
from app.services.storage import StorageService
from app.services.rag import RAGService

router = APIRouter()


@router.post("/index")
async def index_books():
    """
    建立向量索引
    
    处理流程：
    1. 遍历所有已解析的教材
    2. 对每个章节进行分块（约700字/块，75字重叠）
    3. 计算每个chunk的embedding
    4. 存入ChromaDB向量数据库
    
    返回：
    - message: 索引结果信息
    - indexed_books: 已索引的教材数
    - total_chunks: 生成的知识块总数
    """
    result = await RAGService.index_all()
    return result


@router.post("/query")
async def query(req: RAGQueryRequest):
    """
    执行RAG精准问答
    
    处理流程：
    1. 将问题转为向量
    2. 从向量库检索top-k最相关的chunks
    3. 将chunks作为上下文注入LLM prompt
    4. 生成回答并附加来源引用
    
    Args:
        question: 用户问题
        top_k: 检索top-k相关chunks（默认5）
    
    Returns:
        - answer: LLM生成的回答
        - citations: 引用来源列表（教材、章节、页码、相关度）
        - source_chunks: 检索到的原始chunks文本
    """
    result = await RAGService.query(req.question, top_k=req.top_k)
    return result


@router.get("/status")
async def rag_status():
    """
    查询RAG索引状态
    
    Returns:
        - indexed_books: 已索引教材数
        - total_chunks: 总知识块数
        - is_ready: 是否可以进行查询
    """
    return RAGService.get_status()


@router.post("/reset")
async def reset_index():
    """
    重置RAG索引（用于重新构建）
    """
    return RAGService.reset_index()


@router.post("/benchmark")
async def run_benchmark():
    """
    运行RAG性能基准测试
    
    执行标准测试用例集，评估系统质量指标：
    - 关键词覆盖率
    - 引用准确性
    - 幻觉检测
    - 总体评分
    
    Returns:
        完整的测试报告
    """
    try:
        from tests.rag_benchmark import RAGBenchmark
        
        benchmark = RAGBenchmark(RAGService)
        report = await benchmark.run_all_tests()
        
        # 保存报告
        benchmark.save_report("data/rag_benchmark_report.json")
        
        return report
    except Exception as e:
        return {
            "error": str(e),
            "message": "基准测试执行失败"
        }
