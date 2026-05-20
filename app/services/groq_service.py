from groq import Groq

from app.core.config import GROQ_API_KEY
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

    memory = get_conversation_history(
        session_id,
        limit=MAX_CONTEXT_MESSAGES
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful voice assistant. "
                "Keep replies short and conversational."
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
