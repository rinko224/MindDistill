from fastapi import APIRouter

from app.models.schemas import RAGQueryRequest, RAGQueryResponse, RAGStatus
from app.services.storage import StorageService
from app.services.rag import RAGService

router = APIRouter()


@router.post("/index")
async def index_books():
    result = await RAGService.index_all()
    return result


@router.post("/query")
async def query(req: RAGQueryRequest):
    result = await RAGService.query(req.question, top_k=req.top_k)
    return result


@router.get("/status")
async def rag_status():
    return RAGService.get_status()
