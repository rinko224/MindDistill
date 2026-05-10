import uuid
from collections import defaultdict

import numpy as np

from app.models.schemas import GraphData, MergeDecision, MergeResult
from app.services.storage import StorageService
from app.utils.embedding import EmbeddingService


class MergerService:
    """跨教材知识图谱整合服务，支持基于语义相似度的节点合并。"""

    # 余弦相似度阈值，超过则认为两个节点指向同一概念
    SIMILARITY_THRESHOLD = 0.82

    @classmethod
    def merge_all(cls):
        """
        对所有已构建的知识图谱执行跨教材整合。

        策略：
        1. 按 category 分组，避免跨类别误匹配。
        2. 对每个 category 内的节点名称计算 Embedding。
        3. 计算两两余弦相似度，使用贪婪聚类将高相似节点合并。
        4. 生成 MergeDecision 并构建合并后的图谱。
        """
        all_nodes = []
        all_edges = []
        for graph in StorageService.graphs.values():
            all_nodes.extend(graph.nodes)
            all_edges.extend(graph.edges)

        if not all_nodes:
            StorageService.merge_decisions = []
            cls.build_merged_graph()
            StorageService.save_all()
            return

        # 按 category 分组，减少无关比较并提升性能
        category_groups = defaultdict(list)
        for node in all_nodes:
            category_groups[node.category].append(node)

        decisions = []
        merged_groups = []  # 每个元素是一个 List[KnowledgeNode]

        for category, nodes in category_groups.items():
            if len(nodes) == 1:
                merged_groups.append([nodes[0]])
                continue

            # 获取节点名称的向量表示（已归一化）
            names = [n.name for n in nodes]
            embeddings = EmbeddingService.encode(names)
            embeddings = np.array(embeddings, dtype=np.float32)

            # 防御性再次归一化，确保点积即余弦相似度
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / (norms + 1e-8)

            # 贪婪聚类：以第一个未分配节点为锚点，吸收所有相似节点
            used = set()
            for i in range(len(nodes)):
                if i in used:
                    continue
                group = [nodes[i]]
                used.add(i)
                for j in range(i + 1, len(nodes)):
                    if j in used:
                        continue
                    sim = float(np.dot(embeddings[i], embeddings[j]))
                    if sim >= cls.SIMILARITY_THRESHOLD:
                        group.append(nodes[j])
                        used.add(j)
                merged_groups.append(group)

        # 根据聚类结果生成整合决策
        for group in merged_groups:
            if len(group) > 1:
                # 取名称最短的节点作为合并后的代表名称
                rep_node = min(group, key=lambda n: len(n.name))
                names_str = ", ".join(n.name for n in group)
                decision_id = f"merge_{uuid.uuid4().hex[:8]}"
                decisions.append(
                    MergeDecision(
                        decision_id=decision_id,
                        action="merge",
                        affected_nodes=[n.id for n in group],
                        result_node=f"merged_{rep_node.name}",
                        reason=f"语义相似度超过阈值 ({cls.SIMILARITY_THRESHOLD})，合并节点: {names_str}",
                        confidence=0.9,
                    )
                )
            else:
                decision_id = f"keep_{uuid.uuid4().hex[:8]}"
                decisions.append(
                    MergeDecision(
                        decision_id=decision_id,
                        action="keep",
                        affected_nodes=[group[0].id],
                        result_node=None,
                        reason=f"'{group[0].name}'为单个教材独有或语义不重叠，予以保留。",
                        confidence=1.0,
                    )
                )

        StorageService.merge_decisions = decisions
        cls.build_merged_graph()
        StorageService.save_all()

    @classmethod
    def build_merged_graph(cls):
        all_nodes = {}
        all_edges = []
        for graph in StorageService.graphs.values():
            for n in graph.nodes:
                all_nodes[n.id] = n
            all_edges.extend(graph.edges)

        merged_nodes_dict = {}
        node_mapping = {}  # old_id -> new_id

        # 应用 decisions
        for d in StorageService.merge_decisions:
            if d.action == "remove":
                for n_id in d.affected_nodes:
                    node_mapping[n_id] = None  # 表示删除
            elif d.action == "keep":
                for n_id in d.affected_nodes:
                    if n_id in all_nodes:
                        merged_nodes_dict[n_id] = all_nodes[n_id]
                        node_mapping[n_id] = n_id
            elif d.action == "merge":
                if not d.affected_nodes:
                    continue
                # 取第一个节点作为代表
                rep_id = d.affected_nodes[0]
                if rep_id in all_nodes:
                    merged_node = all_nodes[rep_id].copy()
                    merged_node.id = d.result_node or f"merged_{rep_id}"
                    # 累加出现频次
                    merged_node.occurrence = sum(all_nodes[nid].occurrence for nid in d.affected_nodes if nid in all_nodes)
                    merged_nodes_dict[merged_node.id] = merged_node

                    for n_id in d.affected_nodes:
                        node_mapping[n_id] = merged_node.id

        # 处理边
        merged_edges = []
        seen_edges = set()

        for e in all_edges:
            new_source = node_mapping.get(e.source)
            new_target = node_mapping.get(e.target)

            if new_source and new_target and new_source != new_target:
                edge_key = f"{new_source}-{new_target}-{e.relation_type}"
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    merged_edges.append(e.copy(update={"source": new_source, "target": new_target}))

        # 统计字数 (近似)
        original_chars = sum(len(n.definition) for n in all_nodes.values())
        merged_chars = sum(len(n.definition) for n in merged_nodes_dict.values())

        StorageService.merged_graph = GraphData(
            nodes=list(merged_nodes_dict.values()),
            edges=merged_edges
        )
        StorageService.merge_result = MergeResult(
            decisions=StorageService.merge_decisions,
            original_chars=original_chars,
            merged_chars=merged_chars,
            ratio=merged_chars / original_chars if original_chars > 0 else 0,
            original_nodes=len(all_nodes),
            merged_nodes=len(merged_nodes_dict),
        )
