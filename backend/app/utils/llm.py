import os
import json
import re
from dotenv import load_dotenv
load_dotenv()
from typing import Optional

from openai import AsyncOpenAI


class LLMClient:
    client: Optional[AsyncOpenAI] = None
    model: str = "gpt-4o-mini"

    @classmethod
    def init(cls):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if api_key:
            cls.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            cls.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @classmethod
    async def ask(cls, prompt: str, system: str = "", temperature: float = 0.3) -> str:
        if not cls.client:
            cls.init()
        if not cls.client:
            return "[LLM not configured]"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = await cls.client.chat.completions.create(
            model=cls.model,
            messages=messages,
            temperature=temperature,
        )

        print(resp.choices[0].message.content)
        if not resp or not getattr(resp, 'choices', None):
            print(f"LLM API returned unexpected response: {resp}")
            return ""
        return resp.choices[0].message.content or ""

    @classmethod
    async def extract_knowledge(cls, chapter_content: str, chapter_title: str) -> dict:
        prompt = f"""
请从以下教材章节中提取核心知识点及其关系，并确保每个知识点都有完整的定义和元数据。

要求：
1. **控制数量**：每个章节提取 5-8 个最重要的知识点，聚焦核心概念、定理、方法。
2. **严格格式**：必须返回严格的 JSON 格式。
3. **内容完整**：每个节点必须包含 definition（定义）、category（类型）、chapter（章节名） and page（页码）。

【JSON 输出示例】:
{{
  "nodes": [
    {{
      "id": "node_1",
      "name": "局部解剖学",
      "definition": "研究人体各局部内各器官的形态、位置、毗邻等的一门学科。",
      "category": "核心概念",
      "chapter": "{chapter_title}",
      "page": 1
    }}
  ],
  "edges": [
    {{
      "source": "node_1",
      "target": "node_2",
      "relation_type": "contains",
      "description": "局部解剖学包含头部解剖的学习"
    }}
  ]
}}

章节标题：{chapter_title}
章节内容（前3000字）：{chapter_content[:3000]}

请只输出 JSON，不要包含任何解释文字。
"""
        text = await cls.ask(prompt)
        try:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
            return json.loads(text)
        except Exception:
            return {"nodes": [], "edges": []}
