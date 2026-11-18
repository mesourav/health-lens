from fastapi import APIRouter, Request

from app.schemas.chat import ChatRequest, ChatTurn
from app.services.chat_service import respond

router = APIRouter()


@router.post("/chat", response_model=ChatTurn, response_model_exclude_none=True)
async def chat(body: ChatRequest, request: Request) -> ChatTurn:
    """POST /api/chat — one user action in, one assistant turn out."""
    return await respond(body, request.session)
