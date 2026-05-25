from app.core.config import GROQ_AGENT_MODEL, GROQ_API_KEY
from app.tools.conversation_tools import build_conversation_tools
from app.tools.notes_tools import build_notes_tools
from app.tools.search_tools import build_search_tools
from app.tools.todo_tools import build_todo_tools
from app.tools.utility_tools import build_utility_tools


VOICE_AGENT_PROMPT = (
    "You are a helpful voice assistant with tools. "
    "Use tools when the user asks you to remember notes, manage todos, "
    "search previous conversation, calculate, get the current date and time, "
    "or search the internet for current information. "
    "After using a tool, answer naturally and briefly. "
    "Keep spoken replies under 2 short sentences. "
    "Do not mention internal tool names unless the user asks."
)


def build_voice_agent(session_id: str):
    from langchain.agents import create_agent
    from langchain_groq import ChatGroq

    model = ChatGroq(
        model=GROQ_AGENT_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0.2,
        max_tokens=180
    )

    tools = [
        *build_notes_tools(session_id),
        *build_todo_tools(session_id),
        *build_conversation_tools(session_id),
        *build_utility_tools(),
        *build_search_tools()
    ]

    return create_agent(
        model=model,
        tools=tools,
        system_prompt=VOICE_AGENT_PROMPT
    )
