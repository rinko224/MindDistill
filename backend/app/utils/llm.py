import os
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
请从以下教材章节中提取核心知识点及其关系，以严格 JSON 格式返回。

要求：
- 知识点类型至少包含：核心概念、定理、方法、现象
- 关系类型至少包含：prerequisite（前置依赖）、contains（包含）、parallel（并列）、applies_to（应用）
- 每个知识点需包含：id、name、definition、category、chapter、page
- 每条关系需包含：source、target、relation_type、description

【JSON 输出示例（Few-shot）】:
{{
  "nodes": [
    {{
      "id": "node_1",
      "name": "局部解剖学",
      "definition": "研究人体各局部内各器官的形态、位置、毗邻等的一门学科。",
      "category": "核心概念",
      "chapter": "第一章 头部",
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
章节内容（前2000字）：{chapter_content[:2000]}

请只输出 JSON，不要包含任何解释文字。
"""
        text = await cls.ask(prompt)
        import json
        import re
        try:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
            return json.loads(text)
        except Exception:
            return {"nodes": [], "edges": []}
