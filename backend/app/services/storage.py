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
            # 自动清洗：只加载在 books 中存在的图谱，防止 ghost 数据持久化
            cls.graphs = {k: GraphData(**v) for k, v in graphs_data.items() if k in cls.books}
            if len(cls.graphs) < len(graphs_data):
                print(f"Sanitized {len(graphs_data) - len(cls.graphs)} orphaned graph(s).")

        merged_graph_data = cls.load_json("data/merged_graph.json")
        if merged_graph_data:
            cls.merged_graph = GraphData(**merged_graph_data)

        decisions_data = cls.load_json("data/merge_decisions.json")
        if decisions_data:
            cls.merge_decisions = [MergeDecision(**d) for d in decisions_data]

        result_data = cls.load_json("data/merge_result.json")
        if result_data:
            cls.merge_result = MergeResult(**result_data)

    @classmethod
    def save_all(cls):
        books_data = {k: v.model_dump() for k, v in cls.books.items()}
        cls.save_json("data/books.json", books_data)

        graphs_data = {k: v.model_dump() for k, v in cls.graphs.items()}
        cls.save_json("data/graphs.json", graphs_data)

        cls.save_json("data/merged_graph.json", cls.merged_graph.model_dump() if cls.merged_graph else None)
        cls.save_json("data/merge_decisions.json", [d.model_dump() for d in cls.merge_decisions])
        cls.save_json("data/merge_result.json", cls.merge_result.model_dump() if cls.merge_result else None)

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
