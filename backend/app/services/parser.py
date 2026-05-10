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
                import fitz
                doc = fitz.open(file_path)
                book.total_pages = doc.page_count
                doc.close()
                chapters = cls._parse_pdf(file_path)
            elif book.format in ["md", "markdown", "txt"]:
                book.total_pages = 1
                chapters = cls._parse_text(file_path)
            else:
                chapters = []
                book.total_pages = 0

            book.chapters = chapters
            book.total_chars = sum(c.char_count for c in chapters)
            book.status = "completed"
        except Exception as e:
            print(f"Parse error: {e}")
            book.status = "failed"
        finally:
            StorageService.save_all()

    @classmethod
    def _parse_pdf(cls, file_path: str) -> List[Chapter]:
        import fitz  # PyMuPDF
        import uuid
        chapters = []
        doc = fitz.open(file_path)
        current_chapter = None
        # 改进正则表达式：匹配行首的第X章，后面跟随非空字符，且不应包含过多的点（避开目录）
        chapter_pattern = re.compile(r"^\s*(第[一二三四五六七八九十\d]+章\s+[^\n\.]{2,50})", re.MULTILINE)
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # 过滤目录页：如果一页内出现过多匹配项，通常是目录
            all_matches = list(chapter_pattern.finditer(text))
            if len(all_matches) > 5:
                if current_chapter:
                    current_chapter.content += "\n" + text
                    current_chapter.page_end = page_num + 1
                    current_chapter.char_count = len(current_chapter.content)
                continue

            if not all_matches:
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
                for match in all_matches:
                    start_idx = match.start()
                    title = match.group(1).strip()
                    
                    # 进一步过滤：如果标题包含过多连续的点，可能是目录项
                    if "...." in text[start_idx:start_idx+100]:
                        continue
                        
                    # 过滤掉与当前章节标题相同的页眉/页脚重复匹配
                    if current_chapter and title == current_chapter.title:
                        continue

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
                
                if current_chapter:
                    current_chapter.content += "\n" + text[last_idx:]
                    current_chapter.char_count = len(current_chapter.content)

        if current_chapter:
            chapters.append(current_chapter)
            
        doc.close()
        # 最终去重：防止某些情况下产生的空章节或极短章节重复
        final_chapters = []
        for c in chapters:
            if not final_chapters or c.title != final_chapters[-1].title:
                final_chapters.append(c)
            else:
                final_chapters[-1].content += "\n" + c.content
                final_chapters[-1].page_end = c.page_end
                final_chapters[-1].char_count = len(final_chapters[-1].content)
        
        return final_chapters

    @classmethod
    def _parse_text(cls, file_path: str) -> List[Chapter]:
        import uuid
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        chapters = []
        # 改进：Markdown 仅匹配一级标题 # ，或者匹配 第X章
        # 且要求标题后紧跟空格，避免匹配像 ## 这样的子标题
        chapter_pattern = re.compile(r"^(?:#\s+|第[一二三四五六七八九十\d]+章\s+)(.*)", re.MULTILINE)
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
            
            # 过滤掉过短或过长的“标题”
            if len(title) > 100 or len(title) < 2:
                continue

            start_idx = match.start()
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
            content = text[start_idx:end_idx].strip()
            
            # 避免重复标题导致的误切分
            if chapters and title == chapters[-1].title:
                chapters[-1].content += "\n" + content
                chapters[-1].char_count = len(chapters[-1].content)
                continue

            chapters.append(Chapter(
                chapter_id=str(uuid.uuid4()),
                title=title,
                page_start=1,
                page_end=1,
                content=content,
                char_count=len(content)
            ))
            
        return chapters
