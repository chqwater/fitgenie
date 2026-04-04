import sqlite3
import os
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "fitgenie.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                date        TEXT NOT NULL,
                weight_kg   REAL,
                steps       INTEGER,
                calories    INTEGER,
                workout     INTEGER,
                mood        TEXT,
                UNIQUE(user_id, date),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workout_logs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                date         TEXT NOT NULL,
                muscle_group TEXT NOT NULL,
                exercises    TEXT NOT NULL,
                UNIQUE(user_id, date),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
    print("[Memory] DB ready")


# ── 用户 ──────────────────────────────────────────────────

def create_user(username: str, password_hash: str, profile: dict) -> int:
    now = str(date.today())
    with sqlite3.connect(DB_PATH) as conn:
        try:
            cursor = conn.execute("""
                INSERT INTO users
                    (username, password_hash, name, age, weight_kg,
                     height_cm, goal, activity_level, dietary_pref,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                password_hash,
                profile["name"],
                profile["age"],
                profile["weight_kg"],
                profile["height_cm"],
                profile["goal"],
                profile["activity_level"],
                profile["dietary_pref"],
                now, now,
            ))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"用户名 '{username}' 已存在")


def get_user_by_username(username: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("""
            SELECT id, username, password_hash, name, age,
                   weight_kg, height_cm, goal, activity_level, dietary_pref
            FROM users WHERE username = ?
        """, (username,)).fetchone()
    if not row:
        return None
    keys = ["id", "username", "password_hash", "name", "age",
            "weight_kg", "height_cm", "goal", "activity_level", "dietary_pref"]
    return dict(zip(keys, row))


def get_user_by_id(user_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("""
            SELECT id, username, name, age, weight_kg,
                   height_cm, goal, activity_level, dietary_pref
            FROM users WHERE id = ?
        """, (user_id,)).fetchone()
    if not row:
        return None
    keys = ["id", "username", "name", "age", "weight_kg",
            "height_cm", "goal", "activity_level", "dietary_pref"]
    return dict(zip(keys, row))


def update_user(user_id: int, updates: dict):
    if not updates:
        return
    now = str(date.today())
    fields = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [now, user_id]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            f"UPDATE users SET {fields}, updated_at = ? WHERE id = ?",
            values
        )
        conn.commit()


# ── 每日日志 ──────────────────────────────────────────────

def save_daily_log(log: dict, user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO daily_logs
                (user_id, date, weight_kg, steps, calories, workout, mood)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            log["date"],
            log.get("weight_kg"),
            log.get("steps"),
            log.get("calories_intake"),
            int(log.get("workout_done", False)),
            log.get("mood", "neutral"),
        ))
        conn.commit()
    print(f"[Memory] Saved log: {log['date']}")


def get_recent_weights(user_id: int, days: int = 7) -> list[float]:
    cutoff = str(date.today() - timedelta(days=days))
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT weight_kg FROM daily_logs
            WHERE user_id = ? AND date >= ? AND weight_kg IS NOT NULL
            ORDER BY date ASC
        """, (user_id, cutoff)).fetchall()
    return [r[0] for r in rows]


def get_recent_logs(user_id: int, days: int = 7) -> list[dict]:
    cutoff = str(date.today() - timedelta(days=days))
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT date, weight_kg, steps, calories, workout, mood
            FROM daily_logs
            WHERE user_id = ? AND date >= ?
            ORDER BY date DESC
        """, (user_id, cutoff)).fetchall()
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
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT workout FROM daily_logs
            WHERE user_id = ?
            ORDER BY date DESC LIMIT 30
        """, (user_id,)).fetchall()
    streak = 0
    for (workout,) in rows:
        if workout:
            streak += 1
        else:
            break
    return streak


# ── 训练记录 ──────────────────────────────────────────────

def save_workout_log(user_id: int, date_str: str, muscle_group: str, exercises: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO workout_logs
                (user_id, date, muscle_group, exercises)
            VALUES (?, ?, ?, ?)
        """, (user_id, date_str, muscle_group, exercises))
        conn.commit()


def get_recent_workouts(user_id: int, days: int = 7) -> list[dict]:
    cutoff = str(date.today() - timedelta(days=days))
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT date, muscle_group, exercises
            FROM workout_logs
            WHERE user_id = ? AND date >= ?
            ORDER BY date DESC
        """, (user_id, cutoff)).fetchall()
    return [
        {"date": r[0], "muscle_group": r[1], "exercises": r[2]}
        for r in rows
    ]