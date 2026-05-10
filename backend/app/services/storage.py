import json
import os
from typing import Dict, List, Optional

from app.models.schemas import Textbook, GraphData, MergeDecision, MergeResult


class StorageService:
    books: Dict[str, Textbook] = {}
    graphs: Dict[str, GraphData] = {}
    merged_graph: Optional[GraphData] = None
    merge_decisions: List[MergeDecision] = []
    merge_result: Optional[MergeResult] = None
    chat_history: List[dict] = []

    @classmethod
    def load_all(cls):
        books_data = cls.load_json("data/books.json")
        if books_data:
            cls.books = {k: Textbook(**v) for k, v in books_data.items()}
            
        graphs_data = cls.load_json("data/graphs.json")
        if graphs_data:
            cls.graphs = {k: GraphData(**v) for k, v in graphs_data.items()}

    @classmethod
    def save_all(cls):
        books_data = {k: v.model_dump() for k, v in cls.books.items()}
        cls.save_json("data/books.json", books_data)
        
        graphs_data = {k: v.model_dump() for k, v in cls.graphs.items()}
        cls.save_json("data/graphs.json", graphs_data)

    @classmethod
    def save_json(cls, path: str, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_json(cls, path: str):
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
