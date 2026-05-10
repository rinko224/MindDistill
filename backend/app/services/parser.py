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
        import fitz
        import uuid
        import re
        
        chapters = []
        doc = fitz.open(file_path)
        current_chapter = None
        # 匹配 "第 X 章" 格式，X 可以是数字或中文数字
        chapter_pattern = re.compile(r"^\s*(第\s*[一二三四五六七八九十\d]+\s*章\s*[^\n\.]{2,60})", re.MULTILINE)
        
        def normalize_title(t):
            return re.sub(r"[\s\d一二三四五六七八九十章\.,，。·\-_]", "", t)

        last_chapter_num = 0
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # 目录页深度过滤
            if "目录" in text[:200] or "CONTENTS" in text[:200].upper():
                if current_chapter:
                    current_chapter.content += "\n" + text
                continue

            lines = text.split('\n')
            page_content_accum = ""
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                match = chapter_pattern.match(line)
                is_real_heading = False
                
                if match:
                    title = match.group(1).strip()
                    # 提取数字进行顺序校验
                    num_match = re.search(r"([一二三四五六七八九十\d]+)", title)
                    current_num = 0
                    if num_match:
                        # 简单转换或保留原样用于比较
                        num_str = num_match.group(1)
                        # 这里简单处理：如果是连续增长或相近，则可能是真标题
                        is_real_heading = True 

                    # 1. 长度校验
                    if len(title) < 3 or len(title) > 60: is_real_heading = False
                    
                    # 2. 页眉/页脚校验：如果和当前章节标题高度相似，则是重复
                    if current_chapter and normalize_title(title) == normalize_title(current_chapter.title):
                        is_real_heading = False
                        
                    # 3. 目录项校验：后面紧跟数字或过多点
                    if "...." in line or re.search(r"\s+\d+\s*$", line):
                        is_real_heading = False

                if is_real_heading:
                    # 保存前一章
                    if current_chapter:
                        current_chapter.content += "\n" + page_content_accum
                        current_chapter.page_end = page_num + 1
                        current_chapter.char_count = len(current_chapter.content)
                        chapters.append(current_chapter)
                    
                    # 开启新章
                    current_chapter = Chapter(
                        chapter_id=str(uuid.uuid4()),
                        title=title,
                        page_start=page_num + 1,
                        page_end=page_num + 1,
                        content="",
                        char_count=0
                    )
                    page_content_accum = "" # 重置当前页积累
                else:
                    page_content_accum += "\n" + line

            if current_chapter:
                current_chapter.content += "\n" + page_content_accum
                current_chapter.page_end = page_num + 1

        if current_chapter:
            chapters.append(current_chapter)
            
        doc.close()
        
        # 最终清洗：合并过短的章节（可能是误切的标题或装饰行）
        final_chapters = []
        for c in chapters:
            if not final_chapters:
                final_chapters.append(c)
            elif len(c.content) < 200 and c.title != "前言": # 如果内容过少，合并到上一章
                final_chapters[-1].content += f"\n\n{c.title}\n{c.content}"
                final_chapters[-1].page_end = c.page_end
            else:
                final_chapters.append(c)
                
        return final_chapters

    @classmethod
    def _parse_text(cls, file_path: str) -> List[Chapter]:
        import uuid
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        chapters = []
        # 改进：Markdown 仅匹配一级标题 # ，或者匹配 第X章
        # 且要求标题后紧跟空格，避免匹配像 ## 这样的子标题。同时兼容 "第2 章"
        chapter_pattern = re.compile(r"^(?:#\s+|第[一二三四五六七八九十\d]+\s*章\s+)(.*)", re.MULTILINE)
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
