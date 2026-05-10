from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat import ChatService

router = APIRouter()


@router.post("/")
async def chat(req: ChatRequest):
    reply = await ChatService.chat(req.messages)
    return ChatResponse(reply=reply)
