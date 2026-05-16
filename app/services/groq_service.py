from groq import Groq

from app.core.config import GROQ_API_KEY
from app.services.cache_service import (
    get_session_memory,
    add_message
)

client = Groq(api_key=GROQ_API_KEY)


async def generate_response(
    session_id: str,
    user_message: str
):

    memory = get_session_memory(session_id)

    add_message(
        session_id,
        "user",
        user_message
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful voice assistant. "
                "Keep replies short and conversational."
            )
        }
    ] + memory

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=60
    )

    ai_response = (
        response.choices[0]
        .message.content
    )

    add_message(
        session_id,
        "assistant",
        ai_response
    )

    return ai_response