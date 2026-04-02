import sqlite3

conn = sqlite3.connect("vpered.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
login TEXT UNIQUE,
password TEXT,
avatar TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS posts(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
content TEXT,
image TEXT,
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
user_id INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS comments(
id INTEGER PRIMARY KEY AUTOINCREMENT,
text TEXT,
user_id INTEGER,
post_id INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS likes(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
post_id INTEGER
)
""")

conn.commit()
conn.close()
print("DB ready")