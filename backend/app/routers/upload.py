import os
import uuid
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

from app.models.schemas import Textbook
from app.services.storage import StorageService
from app.services.rag import RAGService

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


@router.delete("/{book_id}")
async def delete_book(book_id: str):
    """
    删除教材及其相关数据
    
    删除内容：
    - 从内存中移除教材数据
    - 删除上传的原始文件
    - 删除关联的知识图谱
    - 删除关联的向量索引
    """
    try:
        # 从内存中移除
        if book_id in StorageService.books:
            del StorageService.books[book_id]
        
        # 从知识图谱中移除
        if book_id in StorageService.graphs:
            del StorageService.graphs[book_id]
        
        # 删除上传的文件
        for file in os.listdir(UPLOAD_DIR):
            if file.startswith(book_id):
                file_path = os.path.join(UPLOAD_DIR, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    
        # 删除向量索引
        RAGService.delete_book(book_id)
        
        # 持久化保存
        StorageService.save_all()
        
        return {
            "success": True,
            "message": f"教材 {book_id} 已删除"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "删除失败"
        }
