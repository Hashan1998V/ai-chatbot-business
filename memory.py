import sqlite3

DATABASE = "app.db"


def init_memory_table():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            memory_text TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_user_memory(email):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT memory_text FROM user_memory WHERE email = ?", (email,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return ""

    return "\n".join([row[0] for row in rows])


def save_memory(email, memory_text):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_memory (email, memory_text) VALUES (?, ?)",
        (email, memory_text)
    )
    conn.commit()
    conn.close()