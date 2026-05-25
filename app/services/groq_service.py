from groq import Groq

from app.core.config import GROQ_API_KEY
from app.core.logger import logger
from app.services.memory_service import (
    get_conversation_history,
    save_message
)
from app.tools.search_tools import search_internet, should_search_internet

client = Groq(api_key=GROQ_API_KEY)

MAX_CONTEXT_MESSAGES = 20
GROQ_MODEL = "llama-3.1-8b-instant"


async def generate_response(
    session_id: str,
    user_message: str
):
    if should_search_internet(user_message):
        return await generate_search_grounded_response(
            session_id,
            user_message
        )

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


async def generate_search_grounded_response(
    session_id: str,
    user_message: str
):
    logger.info(
        "event=internet_search_started query=%s",
        user_message
    )

    search_results = await search_internet(
        user_message
    )

    logger.info(
        "event=internet_search_completed result_chars=%s result_preview=%s",
        len(search_results),
        search_results[:250].replace("\n", " ")
    )

    if search_results.startswith((
        "Internet search is not configured",
        "Internet search failed",
        "Search query is empty",
        "No search results found"
    )):
        return search_results

    memory = get_conversation_history(
        session_id,
        limit=8
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful voice assistant. "
                "Answer only from the provided internet search results. "
                "Do not invent facts, questions, prices, dates, or public reactions. "
                "If the results do not contain the exact information requested, say that clearly. "
                "For official exam-paper questions, only list questions that appear explicitly in the search results. "
                "For prices, give the exact available price and timestamp if present. "
                "Mention one source name when useful, but do not read URLs aloud. "
                "Keep normal spoken replies under 2 short sentences, unless the user asks for a list."
            )
        }
    ] + memory + [
        {
            "role": "user",
            "content": (
                f"User question: {user_message}\n\n"
                f"Internet search results:\n{search_results}"
            )
        }
    ]

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=180
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
