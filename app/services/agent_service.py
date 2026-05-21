from app.services.memory_service import (
    get_conversation_history,
    save_message
)


MAX_CONTEXT_MESSAGES = 20


def _extract_text_content(content) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(text)
        return " ".join(parts)

    return str(content or "")


def _extract_final_response(agent_result) -> str:
    messages = agent_result.get("messages", [])

    for message in reversed(messages):
        content = (
            message.get("content")
            if isinstance(message, dict)
            else getattr(message, "content", "")
        )
        text = _extract_text_content(content).strip()
        if text:
            return text

    return ""


async def generate_agent_response(
    session_id: str,
    user_message: str
) -> str:
    from app.agents.voice_agent import build_voice_agent

    memory = get_conversation_history(
        session_id,
        limit=MAX_CONTEXT_MESSAGES
    )

    messages = memory + [
        {
            "role": "user",
            "content": user_message
        }
    ]

    agent = build_voice_agent(
        session_id
    )

    result = await agent.ainvoke(
        {
            "messages": messages
        }
    )

    ai_response = _extract_final_response(
        result
    )

    if not ai_response:
        raise RuntimeError("LangChain agent returned an empty response")

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
