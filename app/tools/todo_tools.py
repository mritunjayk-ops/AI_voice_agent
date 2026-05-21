from app.services import tool_storage_service


def build_todo_tools(session_id: str):
    from langchain.tools import tool

    @tool
    def add_todo(task: str) -> str:
        """Add a new todo task for the user."""
        cleaned_task = task.strip()
        if not cleaned_task:
            return "No todo was added because the task was empty."

        todo_id = tool_storage_service.add_todo(
            session_id,
            cleaned_task
        )
        return f"Added todo {todo_id}."

    @tool
    def list_todos(include_completed: bool = False, limit: int = 10) -> str:
        """List the user's todo tasks. Defaults to pending todos only."""
        safe_limit = max(1, min(limit, 20))
        todos = tool_storage_service.list_todos(
            session_id,
            include_completed,
            safe_limit
        )
        if not todos:
            return "No todos found."

        lines = []
        for todo in todos:
            status = "done" if todo["completed"] else "pending"
            lines.append(f"{todo['id']}. [{status}] {todo['task']}")

        return "\n".join(lines)

    @tool
    def complete_todo(todo_id: int) -> str:
        """Mark a todo task as complete by its numeric id."""
        if todo_id <= 0:
            return "Please provide a valid todo id."

        completed = tool_storage_service.complete_todo(
            session_id,
            todo_id
        )
        if not completed:
            return "I could not find a pending todo with that id."

        return f"Completed todo {todo_id}."

    return [
        add_todo,
        list_todos,
        complete_todo
    ]
