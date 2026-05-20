import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "app.db"


def get_db_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the table if it does not exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Commit changes and close the connection
    conn.commit()
    conn.close()

# Initialize the database
init_db()

def save_message(session_id, role, message):
    """
    Save a conversation message into the conversation_history table.

    Args:
        session_id (str): The session ID of the conversation.
        role (str): The role of the message sender (e.g., 'user', 'assistant').
        message (str): The message content.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Use parameterized query to prevent SQL injection
    cursor.execute(
        """
        INSERT INTO conversation_history (session_id, role, message)
        VALUES (?, ?, ?)
        """,
        (session_id, role, message)
    )

    # Commit changes and close the connection
    conn.commit()
    conn.close()

def get_conversation_history(session_id, limit=None):
    """
    Retrieve conversation history for a given session ID.

    Args:
        session_id (str): The session ID of the conversation.

    Returns:
        list[dict]: A list of messages ordered by timestamp, each represented as a dictionary.
    """
    if limit is not None and limit <= 0:
        return []

    conn = get_db_connection()
    cursor = conn.cursor()

    if limit is None:
        cursor.execute(
            """
            SELECT role, message
            FROM conversation_history
            WHERE session_id = ?
            ORDER BY timestamp ASC, id ASC
            """,
            (session_id,)
        )

    else:
        cursor.execute(
            """
            SELECT role, message
            FROM (
                SELECT id, role, message, timestamp
                FROM conversation_history
                WHERE session_id = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
            )
            ORDER BY timestamp ASC, id ASC
            """,
            (session_id, limit)
        )

    # Fetch all rows and format them as a list of dictionaries
    rows = cursor.fetchall()
    conversation = [
        {"role": row[0], "content": row[1]} for row in rows
    ]

    # Close the connection
    conn.close()

    return conversation

