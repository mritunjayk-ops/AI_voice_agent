from fastapi import APIRouter, HTTPException, Response

from app.models.chat_models import (
    ChatRequest,
    ChatResponse
)
from app.services.groq_service import generate_response
from app.services.session_service import resolve_session_id


router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest,
    http_response: Response
):

    try:
        session_id = resolve_session_id(
            request.session_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    http_response.headers["X-Session-ID"] = session_id

    response = await generate_response(
        session_id,
        request.user_message
    )

    return ChatResponse(
        user_message=request.user_message,
        response=response,
        session_id=session_id
    )
