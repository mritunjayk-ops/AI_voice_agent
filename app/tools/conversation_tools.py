from app.services import tool_storage_service


def build_conversation_tools(session_id: str):
    from langchain.tools import tool

    @tool
    def search_conversation_history(query: str, limit: int = 5) -> str:
        """Search earlier messages from this conversation by keyword."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return "Please provide a search keyword."

        safe_limit = max(1, min(limit, 10))
        messages = tool_storage_service.search_conversation(
            session_id,
            cleaned_query,
            safe_limit
        )
        if not messages:
            return "No matching conversation messages found."

        return "\n".join(
            f"{message['role']}: {message['message']}"
            for message in messages
        )

    return [
        search_conversation_history
    ]
