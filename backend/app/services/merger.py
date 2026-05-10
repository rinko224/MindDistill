from app.models.schemas import GraphData, MergeDecision, MergeResult
from app.services.storage import StorageService
from app.utils.embedding import EmbeddingService


class MergerService:
    @classmethod
    async def merge_all(cls):
        all_nodes = []
        for graph in StorageService.graphs.values():
            all_nodes.extend(graph.nodes)

        # TODO:
        # 1. 计算所有节点的 embedding
        # 2. 相似度聚类，识别重复知识点
        # 3. 生成整合决策（merge / keep / remove）
        # 4. 控制总字数 <= 原始 30%
        # 5. 构建合并后的 merged_graph

        StorageService.merge_decisions = []
        StorageService.merge_result = MergeResult(
            decisions=[],
            original_chars=0,
            merged_chars=0,
            ratio=0.0,
            original_nodes=len(all_nodes),
            merged_nodes=0,
        )
