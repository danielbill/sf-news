import sqlite3

conn = sqlite3.connect("data/db/timeline_2026-01-28.sqlite")
cur = conn.cursor()
cur.execute("SELECT title, source, timestamp FROM articles WHERE title LIKE '%深圳%'")
rows = cur.fetchall()
for r in rows:
    print(f"Title: {r[0][:60]}...")
    print(f"Source: {r[1]}")
    print(f"Time: {r[2]}")
    print("---")
