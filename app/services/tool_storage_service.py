from app.services.memory_service import get_db_connection


def init_tool_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            task TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        )
        """
    )

    conn.commit()
    conn.close()


init_tool_tables()


def add_note(session_id: str, note: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO notes (session_id, note)
        VALUES (?, ?)
        """,
        (session_id, note.strip())
    )
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return int(note_id)


def list_notes(session_id: str, limit: int = 5) -> list[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, note, created_at
        FROM notes
        WHERE session_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (session_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": row[0], "note": row[1], "created_at": row[2]}
        for row in rows
    ]


def search_notes(session_id: str, query: str, limit: int = 5) -> list[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, note, created_at
        FROM notes
        WHERE session_id = ?
          AND note LIKE ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (session_id, f"%{query.strip()}%", limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": row[0], "note": row[1], "created_at": row[2]}
        for row in rows
    ]


def add_todo(session_id: str, task: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO todos (session_id, task)
        VALUES (?, ?)
        """,
        (session_id, task.strip())
    )
    todo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return int(todo_id)


def list_todos(
    session_id: str,
    include_completed: bool = False,
    limit: int = 10
) -> list[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()

    if include_completed:
        cursor.execute(
            """
            SELECT id, task, completed, created_at, completed_at
            FROM todos
            WHERE session_id = ?
            ORDER BY completed ASC, created_at DESC, id DESC
            LIMIT ?
            """,
            (session_id, limit)
        )
    else:
        cursor.execute(
            """
            SELECT id, task, completed, created_at, completed_at
            FROM todos
            WHERE session_id = ?
              AND completed = 0
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (session_id, limit)
        )

    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "task": row[1],
            "completed": bool(row[2]),
            "created_at": row[3],
            "completed_at": row[4]
        }
        for row in rows
    ]


def complete_todo(session_id: str, todo_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE todos
        SET completed = 1,
            completed_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
          AND id = ?
          AND completed = 0
        """,
        (session_id, todo_id)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def search_conversation(
    session_id: str,
    query: str,
    limit: int = 5
) -> list[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, role, message, timestamp
        FROM conversation_history
        WHERE session_id = ?
          AND message LIKE ?
        ORDER BY timestamp DESC, id DESC
        LIMIT ?
        """,
        (session_id, f"%{query.strip()}%", limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "role": row[1],
            "message": row[2],
            "timestamp": row[3]
        }
        for row in rows
    ]
