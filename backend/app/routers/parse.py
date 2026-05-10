from fastapi import APIRouter, BackgroundTasks

from app.models.schemas import Textbook
from app.services.storage import StorageService
from app.services.parser import ParserService

router = APIRouter()


@router.post("/{book_id}")
async def parse_book(book_id: str, background_tasks: BackgroundTasks):
    book = StorageService.books.get(book_id)
    if not book:
        return {"error": "Book not found"}

    background_tasks.add_task(ParserService.parse, book_id)
    book.status = "parsing"
    return {"message": "Parsing started", "book_id": book_id}


@router.get("/{book_id}/status")
async def parse_status(book_id: str):
    book = StorageService.books.get(book_id)
    if not book:
        return {"error": "Book not found"}
    return {"book_id": book_id, "status": book.status}
