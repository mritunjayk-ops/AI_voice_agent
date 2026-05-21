from groq import Groq

from app.core.config import GROQ_API_KEY
from app.core.logger import logger
from app.services.memory_service import (
    get_conversation_history,
    save_message
)

client = Groq(api_key=GROQ_API_KEY)

MAX_CONTEXT_MESSAGES = 20
GROQ_MODEL = "llama-3.1-8b-instant"


async def generate_response(
    session_id: str,
    user_message: str
):
    try:
        from app.services.agent_service import generate_agent_response

        return await generate_agent_response(
            session_id,
            user_message
        )

    except ImportError as exc:
        logger.warning(
            "LangChain agent dependencies unavailable. Falling back to plain Groq. error=%s",
            exc
        )

    except Exception as exc:
        logger.warning(
            "LangChain agent failed. Falling back to plain Groq. error=%s",
            exc
        )

    return await generate_plain_response(
        session_id,
        user_message
    )


async def generate_plain_response(
    session_id: str,
    user_message: str
):

    memory = get_conversation_history(
        session_id,
        limit=MAX_CONTEXT_MESSAGES
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful voice assistant. "
                "Keep your responses extremely short, conversational, and direct. "
                "Use simple, brief sentences (under 10 words each). "
                "Separate distinct ideas or clauses with periods or question marks immediately "
                "so the speech generation begins instantly. "
                "Keep the entire response under 2 sentences."
            )
        }
    ] + memory + [
        {
            "role": "user",
            "content": user_message
        }
    ]

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=60
    )

    ai_response = (
        response.choices[0]
        .message.content
    )

    save_message(
        session_id,
        "user",
        user_message
    )

    save_message(
        session_id,
        "assistant",
        ai_response
    )

    return ai_response
