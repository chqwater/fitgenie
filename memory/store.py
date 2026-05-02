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
    else:
        pk = "INTEGER PRIMARY KEY AUTOINCREMENT"

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

        # 小助手对话记录
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS assistant_conversations (
                id          {pk},
                user_id     INTEGER NOT NULL,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                created_at  TEXT NOT NULL
            )
        """)

        # 小助手提取的用户偏好（每用户一条，JSON 存储）
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id     INTEGER PRIMARY KEY,
                preferences TEXT NOT NULL,
                updated_at  TEXT NOT NULL
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


# ── 小助手对话 ──────────────────────────────────────────────

def save_assistant_message(user_id: int, role: str, content: str):
    """保存一条对话消息（role: 'user' 或 'assistant'）"""
    import datetime
    p = _ph()
    now = datetime.datetime.now().isoformat()
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            INSERT INTO assistant_conversations (user_id, role, content, created_at)
            VALUES ({p},{p},{p},{p})
        """, (user_id, role, content, now))
        conn.commit()


def get_assistant_history(user_id: int, limit: int = 20) -> list[dict]:
    """获取最近 N 条对话历史"""
    p = _ph()
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT role, content, created_at FROM assistant_conversations
            WHERE user_id = {p}
            ORDER BY created_at DESC LIMIT {limit}
        """, (user_id,))
        rows = cur.fetchall()
    # 按时间正序返回
    return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in reversed(rows)]


# ── 用户偏好 ──────────────────────────────────────────────

def save_user_preferences(user_id: int, preferences: dict):
    """保存/更新小助手提取的用户偏好"""
    import json, datetime
    p = _ph()
    now = str(datetime.date.today())
    pref_json = json.dumps(preferences, ensure_ascii=False)
    with _get_conn() as conn:
        cur = conn.cursor()
        if DATABASE_URL:
            cur.execute(f"""
                INSERT INTO user_preferences (user_id, preferences, updated_at)
                VALUES ({p},{p},{p})
                ON CONFLICT (user_id) DO UPDATE SET
                    preferences = EXCLUDED.preferences,
                    updated_at = EXCLUDED.updated_at
            """, (user_id, pref_json, now))
        else:
            cur.execute(f"""
                INSERT OR REPLACE INTO user_preferences (user_id, preferences, updated_at)
                VALUES ({p},{p},{p})
            """, (user_id, pref_json, now))
        conn.commit()


def get_user_preferences(user_id: int) -> dict:
    """获取用户偏好，不存在则返回空 dict"""
    import json
    p = _ph()
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT preferences FROM user_preferences WHERE user_id = {p}
        """, (user_id,))
        row = cur.fetchone()
    if not row:
        return {}
    try:
        return json.loads(row[0])
    except Exception:
        return {}