import os
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "fitgenie.db")
DATABASE_URL = os.environ.get("DATABASE_URL")


def _get_conn():
    """统一获取数据库连接"""
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3
        return sqlite3.connect(DB_PATH)


def _ph() -> str:
    """
    占位符：PostgreSQL 用 %s，SQLite 用 ?
    """
    return "%s" if DATABASE_URL else "?"


def init_db():
    # PostgreSQL 用 SERIAL，SQLite 用 AUTOINCREMENT
    if DATABASE_URL:
        pk = "SERIAL PRIMARY KEY"
        unique_conflict = ""
    else:
        pk = "INTEGER PRIMARY KEY AUTOINCREMENT"
        unique_conflict = ""

    with _get_conn() as conn:
        cur = conn.cursor()

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS users (
                id              {pk},
                username        TEXT NOT NULL UNIQUE,
                password_hash   TEXT NOT NULL,
                name            TEXT NOT NULL,
                age             INTEGER NOT NULL,
                weight_kg       REAL NOT NULL,
                height_cm       REAL NOT NULL,
                goal            TEXT NOT NULL,
                activity_level  TEXT NOT NULL,
                dietary_pref    TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            )
        """)

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS daily_logs (
                id          {pk},
                user_id     INTEGER NOT NULL,
                date        TEXT NOT NULL,
                weight_kg   REAL,
                steps       INTEGER,
                calories    INTEGER,
                workout     INTEGER,
                mood        TEXT,
                UNIQUE(user_id, date)
            )
        """)

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS workout_logs (
                id           {pk},
                user_id      INTEGER NOT NULL,
                date         TEXT NOT NULL,
                muscle_group TEXT NOT NULL,
                exercises    TEXT NOT NULL,
                UNIQUE(user_id, date)
            )
        """)

        conn.commit()
    print("[Memory] DB ready")

# ── 用户 ──────────────────────────────────────────────────

def create_user(username: str, password_hash: str, profile: dict) -> int:
    now = str(date.today())
    p = _ph()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(f"""
            INSERT INTO users
                (username, password_hash, name, age, weight_kg,
                 height_cm, goal, activity_level, dietary_pref,
                 created_at, updated_at)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
        """, (
            username, password_hash,
            profile["name"], profile["age"], profile["weight_kg"],
            profile["height_cm"], profile["goal"],
            profile["activity_level"], profile["dietary_pref"],
            now, now,
        ))
        conn.commit()
        user_id = cur.lastrowid
        return user_id
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise ValueError(f"用户名 '{username}' 已存在")
        raise
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict | None:
    p = _ph()
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, username, password_hash, name, age,
                   weight_kg, height_cm, goal, activity_level, dietary_pref
            FROM users WHERE username = {p}
        """, (username,))
        row = cur.fetchone()
    if not row:
        return None
    keys = ["id", "username", "password_hash", "name", "age",
            "weight_kg", "height_cm", "goal", "activity_level", "dietary_pref"]
    return dict(zip(keys, row))


def get_user_by_id(user_id: int) -> dict | None:
    p = _ph()
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, username, name, age, weight_kg,
                   height_cm, goal, activity_level, dietary_pref
            FROM users WHERE id = {p}
        """, (user_id,))
        row = cur.fetchone()
    if not row:
        return None
    keys = ["id", "username", "name", "age", "weight_kg",
            "height_cm", "goal", "activity_level", "dietary_pref"]
    return dict(zip(keys, row))


def update_user(user_id: int, updates: dict):
    if not updates:
        return
    p = _ph()
    now = str(date.today())
    fields = ", ".join(f"{k} = {p}" for k in updates)
    values = list(updates.values()) + [now, user_id]
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE users SET {fields}, updated_at = {p} WHERE id = {p}",
            values
        )
        conn.commit()


def save_daily_log(log: dict, user_id: int):
    p = _ph()
    with _get_conn() as conn:
        cur = conn.cursor()
        if DATABASE_URL:
            # PostgreSQL 用 INSERT ... ON CONFLICT
            cur.execute(f"""
                INSERT INTO daily_logs
                    (user_id, date, weight_kg, steps, calories, workout, mood)
                VALUES ({p},{p},{p},{p},{p},{p},{p})
                ON CONFLICT (user_id, date) DO UPDATE SET
                    weight_kg = EXCLUDED.weight_kg,
                    steps = EXCLUDED.steps,
                    calories = EXCLUDED.calories,
                    workout = EXCLUDED.workout,
                    mood = EXCLUDED.mood
            """, (
                user_id, log["date"], log.get("weight_kg"),
                log.get("steps"), log.get("calories_intake"),
                int(log.get("workout_done", False)), log.get("mood", "neutral"),
            ))
        else:
            # SQLite 用 INSERT OR REPLACE
            cur.execute(f"""
                INSERT OR REPLACE INTO daily_logs
                    (user_id, date, weight_kg, steps, calories, workout, mood)
                VALUES ({p},{p},{p},{p},{p},{p},{p})
            """, (
                user_id, log["date"], log.get("weight_kg"),
                log.get("steps"), log.get("calories_intake"),
                int(log.get("workout_done", False)), log.get("mood", "neutral"),
            ))
        conn.commit()
    print(f"[Memory] Saved log: {log['date']}")


def get_recent_weights(user_id: int, days: int = 7) -> list[float]:
    p = _ph()
    cutoff = str(date.today() - timedelta(days=days))
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT weight_kg FROM daily_logs
            WHERE user_id = {p} AND date >= {p} AND weight_kg IS NOT NULL
            ORDER BY date ASC
        """, (user_id, cutoff))
        rows = cur.fetchall()
    return [r[0] for r in rows]


def get_recent_logs(user_id: int, days: int = 7) -> list[dict]:
    p = _ph()
    cutoff = str(date.today() - timedelta(days=days))
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT date, weight_kg, steps, calories, workout, mood
            FROM daily_logs
            WHERE user_id = {p} AND date >= {p}
            ORDER BY date DESC
        """, (user_id, cutoff))
        rows = cur.fetchall()
    return [
        {
            "date": r[0],
            "weight_kg": r[1],
            "steps": r[2],
            "calories_intake": r[3],
            "workout_done": bool(r[4]),
            "mood": r[5],
        }
        for r in rows
    ]


def get_streak(user_id: int) -> int:
    p = _ph()
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT workout FROM daily_logs
            WHERE user_id = {p}
            ORDER BY date DESC LIMIT 30
        """, (user_id,))
        rows = cur.fetchall()
    streak = 0
    for (workout,) in rows:
        if workout:
            streak += 1
        else:
            break
    return streak


def save_workout_log(user_id: int, date_str: str, muscle_group: str, exercises: str):
    p = _ph()
    with _get_conn() as conn:
        cur = conn.cursor()
        if DATABASE_URL:
            cur.execute(f"""
                INSERT INTO workout_logs (user_id, date, muscle_group, exercises)
                VALUES ({p},{p},{p},{p})
                ON CONFLICT (user_id, date) DO UPDATE SET
                    muscle_group = EXCLUDED.muscle_group,
                    exercises = EXCLUDED.exercises
            """, (user_id, date_str, muscle_group, exercises))
        else:
            cur.execute(f"""
                INSERT OR REPLACE INTO workout_logs
                    (user_id, date, muscle_group, exercises)
                VALUES ({p},{p},{p},{p})
            """, (user_id, date_str, muscle_group, exercises))
        conn.commit()


def get_recent_workouts(user_id: int, days: int = 7) -> list[dict]:
    p = _ph()
    cutoff = str(date.today() - timedelta(days=days))
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT date, muscle_group, exercises
            FROM workout_logs
            WHERE user_id = {p} AND date >= {p}
            ORDER BY date DESC
        """, (user_id, cutoff))
        rows = cur.fetchall()
    return [
        {"date": r[0], "muscle_group": r[1], "exercises": r[2]}
        for r in rows
    ]