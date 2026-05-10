import os
import re
from typing import List

from app.models.schemas import Textbook, Chapter
from app.services.storage import StorageService


class ParserService:
    @classmethod
    async def parse(cls, book_id: str):
        book = StorageService.books.get(book_id)
        if not book:
            return

        file_path = os.path.join("data/uploaded", f"{book_id}.{book.format}")
        if not os.path.exists(file_path):
            book.status = "failed"
            return

        try:
            if book.format == "pdf":
                chapters = cls._parse_pdf(file_path)
            elif book.format in ["md", "markdown", "txt"]:
                chapters = cls._parse_text(file_path)
            else:
                chapters = []

            book.chapters = chapters
            book.total_chars = sum(c.char_count for c in chapters)
            book.status = "completed"
        except Exception as e:
            print(f"Parse error: {e}")
            book.status = "failed"

    @classmethod
    def _parse_pdf(cls, file_path: str) -> List[Chapter]:
        import fitz  # PyMuPDF
        import uuid
        chapters = []
        doc = fitz.open(file_path)
        current_chapter = None
        chapter_pattern = re.compile(r"^\s*(第[一二三四五六七八九十\d]+章.*)", re.MULTILINE)
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text()
            matches = list(chapter_pattern.finditer(text))
            
            if not matches:
                if current_chapter:
                    current_chapter.content += "\n" + text
                    current_chapter.page_end = page_num + 1
                    current_chapter.char_count = len(current_chapter.content)
                else:
                    current_chapter = Chapter(
                        chapter_id=str(uuid.uuid4()),
                        title="前言",
                        page_start=page_num + 1,
                        page_end=page_num + 1,
                        content=text,
                        char_count=len(text)
                    )
            else:
                last_idx = 0
                for match in matches:
                    start_idx = match.start()
                    title = match.group(1).strip()
                    if current_chapter:
                        current_chapter.content += "\n" + text[last_idx:start_idx]
                        current_chapter.page_end = page_num + 1
                        current_chapter.char_count = len(current_chapter.content)
                        chapters.append(current_chapter)
                    
                    current_chapter = Chapter(
                        chapter_id=str(uuid.uuid4()),
                        title=title,
                        page_start=page_num + 1,
                        page_end=page_num + 1,
                        content="",
                        char_count=0
                    )
                    last_idx = start_idx
                current_chapter.content = text[last_idx:]
                current_chapter.char_count = len(current_chapter.content)

        if current_chapter:
            chapters.append(current_chapter)
            
        doc.close()
        return chapters

    @classmethod
    def _parse_text(cls, file_path: str) -> List[Chapter]:
        import uuid
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        chapters = []
        chapter_pattern = re.compile(r"^(?:#\s+|第[一二三四五六七八九十\d]+章)(.*)", re.MULTILINE)
        matches = list(chapter_pattern.finditer(text))
        
        if not matches:
            chapters.append(Chapter(
                chapter_id=str(uuid.uuid4()),
                title="默认章节",
                page_start=1,
                page_end=1,
                content=text,
                char_count=len(text)
            ))
            return chapters
            
        if matches[0].start() > 0:
            pre_text = text[0:matches[0].start()].strip()
            if pre_text:
                chapters.append(Chapter(
                    chapter_id=str(uuid.uuid4()),
                    title="前言",
                    page_start=1,
                    page_end=1,
                    content=pre_text,
                    char_count=len(pre_text)
                ))
                
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            if not title:
                title = match.group(0).strip()
            start_idx = match.start()
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
            content = text[start_idx:end_idx].strip()
            chapters.append(Chapter(
                chapter_id=str(uuid.uuid4()),
                title=title,
                page_start=1,
                page_end=1,
                content=content,
                char_count=len(content)
            ))
            
        return chapters
