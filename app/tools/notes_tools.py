from app.services import tool_storage_service


def build_notes_tools(session_id: str):
    from langchain.tools import tool

    @tool
    def save_note(note: str) -> str:
        """Save an important note the user wants the assistant to remember."""
        cleaned_note = note.strip()
        if not cleaned_note:
            return "No note was saved because the note was empty."

        note_id = tool_storage_service.add_note(
            session_id,
            cleaned_note
        )
        return f"Saved note {note_id}."

    @tool
    def list_saved_notes(limit: int = 5) -> str:
        """List the user's most recent saved notes."""
        safe_limit = max(1, min(limit, 10))
        notes = tool_storage_service.list_notes(
            session_id,
            safe_limit
        )
        if not notes:
            return "No saved notes found."

        return "\n".join(
            f"{note['id']}. {note['note']}"
            for note in notes
        )

    @tool
    def search_saved_notes(query: str, limit: int = 5) -> str:
        """Search the user's saved notes by keyword."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return "Please provide a search keyword."

        safe_limit = max(1, min(limit, 10))
        notes = tool_storage_service.search_notes(
            session_id,
            cleaned_query,
            safe_limit
        )
        if not notes:
            return "No matching saved notes found."

        return "\n".join(
            f"{note['id']}. {note['note']}"
            for note in notes
        )

    return [
        save_note,
        list_saved_notes,
        search_saved_notes
    ]
