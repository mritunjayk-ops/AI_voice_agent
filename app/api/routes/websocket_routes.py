from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logger import logger
from app.services.groq_service import generate_response

router = APIRouter()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):

    await websocket.accept()

    logger.info("WebSocket connection established")

    try:

        while True:

            # RECEIVE MESSAGE
            user_message = await websocket.receive_text()

            logger.info(
                f"WebSocket message received: {user_message}"
            )

            # GENERATE AI RESPONSE
            ai_response = await generate_response(
                "websocket_user",
                user_message
            )

            # SEND RESPONSE
            await websocket.send_text(ai_response)

    except WebSocketDisconnect:

        logger.warning(
            "WebSocket disconnected normally"
        )

    except Exception as e:

        logger.error(
            f"WebSocket Error: {str(e)}"
        )