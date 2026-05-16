from fastapi import APIRouter

from app.models.chat_models import (
    ChatRequest,
    ChatResponse
)
from app.services.groq_service import generate_response


router = APIRouter()


SESSION_ID = "default_user"


@router.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(request: ChatRequest):

    response = await generate_response(
        SESSION_ID,
        request.user_message
    )

    return ChatResponse(
        user_message=request.user_message,
        response=response
    )