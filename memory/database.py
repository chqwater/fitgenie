# memory/database.py
import os
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    """
    有 DATABASE_URL 环境变量时用 PostgreSQL，
    否则降级用 SQLite（本地开发）。
    """
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    else:
        from memory.store import DB_PATH
        return sqlite3.connect(DB_PATH)


def is_postgres() -> bool:
    return DATABASE_URL is not None