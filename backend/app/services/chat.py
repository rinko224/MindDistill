from typing import List

from app.models.schemas import ChatMessage
from app.services.storage import StorageService
from app.utils.llm import LLMClient


class ChatService:
    @classmethod
    async def chat(cls, messages: List[ChatMessage]) -> str:
        # 获取当前的所有决策
        decisions_info = []
        for d in StorageService.merge_decisions:
            node_names = []
            for n_id in d.affected_nodes:
                for graph in StorageService.graphs.values():
                    node = next((n for n in graph.nodes if n.id == n_id), None)
                    if node:
                        node_names.append(node.name)
                        break
            names_str = ", ".join(set(node_names))
            decisions_info.append(f"决策ID: {d.decision_id} | 动作: {d.action} | 涉及知识点: {names_str} | 原因: {d.reason}")
            
        decisions_str = "\n".join(decisions_info)
        if not decisions_str:
            decisions_str = "目前没有整合决策。"

        system_prompt = f"""你是一个学科知识整合助手，负责帮助教师解释整合决策，或者根据教师的要求修改整合决策。
当前的整合决策列表如下：
{decisions_str}

你可以选择正常回复，或者如果你决定需要修改某些决策，请在回复的任意位置（通常在最后）加上一个严格的 JSON 代码块，格式如下：
```json
{{
    "modifications": [
        {{"decision_id": "要修改的决策ID", "action": "新的动作，可选值为 merge, keep, remove"}}
    ]
}}
```
注意：
1. 回复内容对用户要自然友好，不要直接暴露系统内部的 decision_id。
2. 对于要求分开/拆分的请求，应将原本的 'merge' 动作修改为 'keep'。
3. 对于要求删除的请求，将动作修改为 'remove'。
4. 如果不需要修改决策，只需进行普通回复，无需包含 JSON 块。
"""
        
        prompt = ""
        for m in messages[-4:]:
            prompt += f"{m.role}: {m.content}\n"
        
        reply = await LLMClient.ask(prompt, system=system_prompt)
        
        import re
        import json
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", reply, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if "modifications" in data and data["modifications"]:
                    cls._apply_modifications(data["modifications"])
                    reply = reply.replace(match.group(0), "").strip()
            except Exception as e:
                print("Failed to parse modifications:", e)
                
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
