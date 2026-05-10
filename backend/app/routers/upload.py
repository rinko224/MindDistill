import os
import uuid
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

from app.models.schemas import Textbook
from app.services.storage import StorageService

router = APIRouter()

UPLOAD_DIR = "data/uploaded"


@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    book_id = f"book_{uuid.uuid4().hex[:8]}"
    ext = os.path.splitext(file.filename)[1].lower()
    save_path = os.path.join(UPLOAD_DIR, f"{book_id}{ext}")

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    book = Textbook(
        textbook_id=book_id,
        filename=file.filename,
        title=os.path.splitext(file.filename)[0],
        total_pages=0,
        total_chars=0,
        format=ext.lstrip("."),
        status="parsing",
    )
    StorageService.books[book_id] = book
    return {"success": True, "book": book}


@router.get("/")
async def list_uploads():
    books = list(StorageService.books.values())
    return {"books": books, "total": len(books)}
