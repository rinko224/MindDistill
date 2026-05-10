from typing import List

from app.models.schemas import ChatMessage
from app.services.storage import StorageService
from app.utils.llm import LLMClient


class ChatService:
    @classmethod
    async def chat(cls, messages: List[ChatMessage]) -> str:
        # 仅选择关键的合并决策信息，避免上下文过长
        decisions_info = []
        # 只选取 action="merge" 的决策，因为教师通常最关心合并的是否正确
        relevant_decisions = [d for d in StorageService.merge_decisions if d.action == "merge"][:50]
        
        for d in relevant_decisions:
            node_names = []
            for n_id in d.affected_nodes:
                # 快速查找节点名称
                found = False
                for graph in StorageService.graphs.values():
                    node = next((n for n in graph.nodes if n.id == n_id), None)
                    if node:
                        node_names.append(node.name)
                        found = True
                        break
            names_str = ", ".join(set(node_names))
            decisions_info.append(f"决策ID: {d.decision_id} | 当前动作: {d.action} | 涉及知识点: {names_str} | 合并后的代表名: {d.result_node}")
            
        decisions_str = "\n".join(decisions_info)
        if not decisions_str:
            decisions_str = "目前没有复杂的合并决策。"

        system_prompt = f"""你是一个学科知识整合助手。你的任务是：
1. 解释现有的整合决策（为什么合并某些点）。
2. 根据教师的要求修改决策（如：要求分开、删除、或保留某个点）。

【当前关键合并决策列表】：
{decisions_str}

【操作指南】：
- 如果用户说“把 A 和 B 分开”或“A 和 B 不是一个概念”，请找到包含 A 和 B 的决策 ID，将其 action 改为 "keep"。
- 如果用户说“删除 A”，请找到涉及 A 的决策，将其 action 改为 "remove"。
- 在回复用户时，语气要专业且谦虚。

如果你决定修改决策，请在回复末尾附带以下格式的 JSON（严禁修改格式）：
```json
{{
    "modifications": [
        {{"decision_id": "决策ID", "action": "keep/remove/merge"}}
    ]
}}
```
不要向用户直接解释 JSON 内容或 decision_id，只需告知其“已为您调整”。
"""
        
        # 构建对话上下文
        full_prompt = ""
        for m in messages:
            full_prompt += f"{m.role}: {m.content}\n"
        
        reply = await LLMClient.ask(full_prompt, system=system_prompt)
        
        import re
        import json
        # 改进正则表达式，增强容错性
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", reply, re.DOTALL) or re.search(r"(\{.*?\})", reply, re.DOTALL)
        
        if json_match:
            try:
                # 尝试查找包含 modifications 的 JSON
                potential_json = json_match.group(1)
                if '"modifications"' in potential_json:
                    data = json.loads(potential_json)
                    if "modifications" in data and data["modifications"]:
                        cls._apply_modifications(data["modifications"])
                        # 从回复中移除 JSON 部分，保持 UI 整洁
                        reply = re.sub(r"```json.*?```", "", reply, flags=re.DOTALL).strip()
                        reply = re.sub(r"\{.*?\}", "", reply, flags=re.DOTALL).strip() # 备选清理
                        if not reply: reply = "好的，已根据您的要求调整了整合决策并重新构建了图谱。"
            except Exception as e:
                print(f"Failed to parse or apply modifications: {e}")
                
        return reply

    @classmethod
    def _apply_modifications(cls, modifications: List[dict]):
        changed = False
        for mod in modifications:
            decision_id = mod.get("decision_id")
            action = mod.get("action")
            if action not in ["merge", "keep", "remove"]:
                continue
                
            for d in StorageService.merge_decisions:
                if d.decision_id == decision_id:
                    if d.action != action:
                        d.action = action
                        d.reason += f" (已根据用户要求修改为 {action})"
                        changed = True
                    break
        
        if changed:
            from app.services.merger import MergerService
            MergerService.build_merged_graph()
            StorageService.save_all()
