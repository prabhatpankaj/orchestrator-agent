import sqlite3

def run(query: str):
    try:
        conn = sqlite3.connect("local.db")
        cur = conn.cursor()
        cur.execute(query)
        return cur.fetchall()
    except Exception as e:
        return f"SQL Error: {str(e)}"
