"""
AI-Empowered Mental Health Awareness Website with AI Chatbot - one-time data migration
Copies existing rows from the old SQLite database (mindmate.db) into the
new MySQL database, so you don't lose your test users/feedback/stress
history when switching backends.

Run this ONCE, after setting up MySQL and creating tables (i.e. after
running app.py or create_admin.py at least once so tables exist).

Requirements:
    pip install sqlalchemy pymysql
"""

import sqlite3
from werkzeug.security import generate_password_hash
from database import SessionLocal, User, Feedback, StressResult, Admin

SQLITE_PATH = "mindmate.db"  # copy this file from the old mental-backend/ folder

sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row
cur = sqlite_conn.cursor()

db = SessionLocal()

def migrate_table(table_name, model, columns, hash_password_field=False):
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    count = 0
    for row in rows:
        kwargs = {col: row[col] for col in columns if col in row.keys()}
        # Skip if already migrated (basic dedupe on id)
        if "id" in row.keys() and db.query(model).filter(model.id == row["id"]).first():
            continue
        # The old SQLite database stored passwords in PLAIN TEXT. Hash them
        # now during migration so nothing plaintext ever lands in MySQL.
        if hash_password_field and "password" in kwargs and kwargs["password"]:
            kwargs["password"] = generate_password_hash(kwargs["password"])
        db.add(model(**kwargs))
        count += 1
    db.commit()
    print(f"Migrated {count} rows into '{table_name}'")

try:
    migrate_table("users", User, ["id", "email", "password"], hash_password_field=True)
    migrate_table("feedback", Feedback, ["id", "name", "country", "message", "rating"])
    migrate_table("stress_results", StressResult,
                  ["id", "user", "sleep", "bp", "resp", "heart", "stress_level", "advice", "timestamp"])
    migrate_table("admins", Admin,
                  ["id", "username", "password", "email", "created_at", "is_active"],
                  hash_password_field=True)
    print("\nMigration complete.")
except Exception as e:
    print(f"Migration error: {e}")
    db.rollback()
finally:
    db.close()
    sqlite_conn.close()
