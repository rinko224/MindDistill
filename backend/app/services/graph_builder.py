import asyncio
from app.models.schemas import GraphData, KnowledgeNode, KnowledgeEdge
from app.services.storage import StorageService
from app.utils.llm import LLMClient


class GraphBuilderService:
    @classmethod
    async def build(cls, book_id: str):
        book = StorageService.books.get(book_id)
        if not book:
            return

        node_dict = {}
        edges = []
        semaphore = asyncio.Semaphore(5)  # 限制并发数

        async def process_chapter(chapter):
            skip_keywords = ["前言", "序言", "目录", "编委名单", "后记", "参考文献", "附录", "使用说明"]
            if any(kw in chapter.title for kw in skip_keywords):
                return None
            
            async with semaphore:
                try:
                    result = await LLMClient.extract_knowledge(chapter.content, chapter.title)
                    return result, chapter
                except Exception as e:
                    print(f"Error extracting knowledge from chapter {chapter.title}: {e}")
                    return None

        try:
            tasks = [process_chapter(chapter) for chapter in book.chapters]
            results = await asyncio.gather(*tasks)

            edge_dict = {}
            for res in results:
                if not res:
                    continue
                
                result, chapter = res
                chapter_nodes = result.get("nodes", [])
                id_map = {}
                
                for node_data in chapter_nodes:
                    name = node_data.get('name', '')
                    if not name:
                        continue
                    
                    new_id = f"{book_id}_{name}"
                    id_map[str(node_data.get('id', ''))] = new_id
                    
                    if new_id not in node_dict:
                        node_dict[new_id] = KnowledgeNode(
                            id=new_id,
                            name=name,
                            definition=node_data.get('definition', ''),
                            category=node_data.get('category', '概念'),
                            chapter=node_data.get('chapter', chapter.title),
                            page=node_data.get('page', chapter.page_start),
                            textbook_id=book_id,
                            occurrence=1
                        )
                    else:
                        node_dict[new_id].occurrence += 1
                
                chapter_edges = result.get("edges", [])
                for edge_data in chapter_edges:
                    source_old = str(edge_data.get('source', ''))
                    target_old = str(edge_data.get('target', ''))
                    
                    source_new = id_map.get(source_old)
                    target_new = id_map.get(target_old)
                    
                    if source_new and target_new:
                        rtype = edge_data.get('relation_type')
                        if rtype not in ["prerequisite", "parallel", "contains", "applies_to"]:
                            rtype = "parallel"
                        
                        edge_key = f"{source_new}_{target_new}_{rtype}"
                        if edge_key not in edge_dict:
                            edge_dict[edge_key] = KnowledgeEdge(
                                source=source_new,
                                target=target_new,
                                relation_type=rtype,
                                description=edge_data.get('description', '')
                            )

            nodes = list(node_dict.values())
            edges = list(edge_dict.values())
            graph = GraphData(nodes=nodes, edges=edges)
            StorageService.graphs[book_id] = graph
            book.graph_status = "completed"
            StorageService.save_all()
            return graph
        except Exception as e:
            print(f"Graph build error: {e}")
            book.graph_status = "failed"
            StorageService.save_all()
