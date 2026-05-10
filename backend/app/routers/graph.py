from fastapi import APIRouter, BackgroundTasks

from app.services.storage import StorageService
from app.services.graph_builder import GraphBuilderService

router = APIRouter()


@router.post("/build/{book_id}")
async def build_graph(book_id: str, background_tasks: BackgroundTasks):
    book = StorageService.books.get(book_id)
    if not book:
        return {"error": "Book not found"}

    background_tasks.add_task(GraphBuilderService.build, book_id)
    return {"message": "Graph building started", "book_id": book_id}


@router.get("/{book_id}")
async def get_graph(book_id: str):
    graph = StorageService.graphs.get(book_id)
    if not graph:
        return {"error": "Graph not found"}
    return graph


@router.get("/merged")
async def get_merged_graph():
    graph = StorageService.merged_graph
    if not graph:
        return {"error": "Merged graph not found"}
    return graph
