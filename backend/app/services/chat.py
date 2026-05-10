from typing import List

from app.models.schemas import ChatMessage
from app.services.storage import StorageService
from app.utils.llm import LLMClient


class ChatService:
    @classmethod
    async def chat(cls, messages: List[ChatMessage]) -> str:
        # TODO:
        # 1. 解析用户意图（询问原因 / 修改整合方案）
        # 2. 如果是修改意图，调整 merged_graph / merge_decisions
        # 3. 更新 StorageService
        # 4. 调用 LLM 生成回复
        return "收到您的反馈，系统已记录。"
