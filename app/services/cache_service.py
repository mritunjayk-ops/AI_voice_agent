session_memory = {}


def get_session_memory(session_id: str):

    if session_id not in session_memory:

        session_memory[session_id] = []

    return session_memory[session_id]


def add_message(
    session_id: str,
    role: str,
    content: str
):

    if session_id not in session_memory:

        session_memory[session_id] = []

    session_memory[session_id].append(
        {
            "role": role,
            "content": content
        }
    )

    session_memory[session_id] = (
        session_memory[session_id][-10:]
    )