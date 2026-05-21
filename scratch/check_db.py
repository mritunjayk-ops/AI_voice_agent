import sqlite3

def check():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, session_id, role, message, timestamp FROM conversation_history ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    print("Recent rows:")
    for r in rows:
        print(r)
    conn.close()

if __name__ == "__main__":
    check()
