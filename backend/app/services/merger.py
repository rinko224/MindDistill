from app.models.schemas import GraphData, MergeDecision, MergeResult
from app.services.storage import StorageService
from app.utils.embedding import EmbeddingService


class MergerService:
    @classmethod
    async def merge_all(cls):
        all_nodes = []
        all_edges = []
        for graph in StorageService.graphs.values():
            all_nodes.extend(graph.nodes)
            all_edges.extend(graph.edges)

        # 简单策略：按名称精确匹配进行合并
        from collections import defaultdict
        name_groups = defaultdict(list)
        for node in all_nodes:
            name_groups[node.name].append(node)

        import uuid
        decisions = []
        
        for name, nodes in name_groups.items():
            if len(nodes) > 1:
                decision_id = f"merge_{uuid.uuid4().hex[:8]}"
                decisions.append(MergeDecision(
                    decision_id=decision_id,
                    action="merge",
                    affected_nodes=[n.id for n in nodes],
                    result_node=f"merged_{name}",
                    reason=f"多个教材中都包含'{name}'，执行合并以精简内容。",
                    confidence=1.0
                ))
            else:
                decision_id = f"keep_{uuid.uuid4().hex[:8]}"
                decisions.append(MergeDecision(
                    decision_id=decision_id,
                    action="keep",
                    affected_nodes=[nodes[0].id],
                    result_node=None,
                    reason=f"'{name}'为单个教材独有，予以保留。",
                    confidence=1.0
                ))

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
        node_mapping = {} # old_id -> new_id
        
        # 应用 decisions
        for d in StorageService.merge_decisions:
            if d.action == "remove":
                for n_id in d.affected_nodes:
                    node_mapping[n_id] = None # 表示删除
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
