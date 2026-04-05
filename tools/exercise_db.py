# tools/exercise_db.py
# ─────────────────────────────────────────────────────────────────────────────
# ExerciseDB Tool
# 给 Coach Agent 调用的真实动作查询工具
# 按肌群查询动作，返回标准化的动作列表
# ─────────────────────────────────────────────────────────────────────────────

import os
import requests
from functools import lru_cache

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")
BASE_URL = "https://exercisedb.p.rapidapi.com"
HEADERS = {
    "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
    "X-RapidAPI-Key": RAPIDAPI_KEY,
}

# ExerciseDB 的肌群名称映射
# 我们系统用中文，API 用英文
MUSCLE_MAP = {
    "胸": "chest",
    "背": "back",
    "腿": "upper legs",
    "臀": "upper legs",
    "肩": "shoulders",
    "二头": "upper arms",
    "三头": "upper arms",
    "核心": "waist",
    "全身": "upper legs",
}


@lru_cache(maxsize=32)
def get_exercises_by_muscle(muscle_zh: str, limit: int = 8) -> list[dict]:
    """
    按肌群查询动作。
    结果缓存在内存里，同一肌群不重复调用 API。

    返回格式：
    [
        {
            "name": "Barbell Squat",
            "name_zh": "杠铃深蹲",  # 简单翻译
            "equipment": "barbell",
            "target": "quads",
            "gif_url": "https://...",
        },
        ...
    ]
    """
    # 找到对应的英文肌群名
    muscle_en = _find_muscle(muscle_zh)

    try:
        response = requests.get(
            f"{BASE_URL}/exercises/bodyPart/{muscle_en}",
            headers=HEADERS,
            params={"limit": limit, "offset": 0},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()

        return [_format_exercise(ex) for ex in data]

    except Exception as e:
        print(f"[ExerciseDB] ⚠️ API 调用失败: {e}，使用降级数据")
        return _fallback_exercises(muscle_zh)


def _find_muscle(muscle_zh: str) -> str:
    """从中文肌群描述里找到对应的英文 key"""
    for zh, en in MUSCLE_MAP.items():
        if zh in muscle_zh:
            return en
    return "quads"  # 默认


def _format_exercise(ex: dict) -> dict:
    """标准化 API 返回的动作数据"""
    return {
        "name": ex.get("name", ""),
        "name_zh": _translate_name(ex.get("name", "")),
        "equipment": ex.get("equipment", "body weight"),
        "target": ex.get("target", ""),
        "gif_url": ex.get("gifUrl", ""),
    }


def _translate_name(name: str) -> str:
    """
    简单的动作名翻译。
    生产环境可以接入翻译 API，这里用关键词映射。
    """
    translations = {
        "squat": "深蹲",
        "deadlift": "硬拉",
        "bench press": "卧推",
        "push up": "俯卧撑",
        "pull up": "引体向上",
        "row": "划船",
        "curl": "弯举",
        "press": "推举",
        "fly": "飞鸟",
        "lunge": "弓步",
        "plank": "平板支撑",
        "crunch": "卷腹",
        "raise": "侧平举",
        "extension": "伸展",
        "dip": "双杠臂屈伸",
    }
    name_lower = name.lower()
    for en, zh in translations.items():
        if en in name_lower:
            # 保留原名 + 中文
            return f"{zh}（{name}）"
    return name  # 无匹配就返回原名


def _fallback_exercises(muscle_zh: str) -> list[dict]:
    """
    API 调用失败时的降级数据。
    保证系统在无网络或 API 限流时仍能正常运行。
    """
    fallbacks = {
        "胸": [
            {"name": "Push Up", "name_zh": "俯卧撑", "equipment": "body weight", "target": "pectorals", "gif_url": ""},
            {"name": "Dumbbell Bench Press", "name_zh": "哑铃卧推", "equipment": "dumbbell", "target": "pectorals", "gif_url": ""},
            {"name": "Dumbbell Fly", "name_zh": "哑铃飞鸟", "equipment": "dumbbell", "target": "pectorals", "gif_url": ""},
        ],
        "背": [
            {"name": "Pull Up", "name_zh": "引体向上", "equipment": "body weight", "target": "lats", "gif_url": ""},
            {"name": "Dumbbell Row", "name_zh": "哑铃划船", "equipment": "dumbbell", "target": "lats", "gif_url": ""},
        ],
        "腿": [
            {"name": "Squat", "name_zh": "深蹲", "equipment": "body weight", "target": "quads", "gif_url": ""},
            {"name": "Lunge", "name_zh": "弓步蹲", "equipment": "body weight", "target": "quads", "gif_url": ""},
            {"name": "Deadlift", "name_zh": "硬拉", "equipment": "barbell", "target": "glutes", "gif_url": ""},
        ],
        "核心": [
            {"name": "Plank", "name_zh": "平板支撑", "equipment": "body weight", "target": "abs", "gif_url": ""},
            {"name": "Crunch", "name_zh": "卷腹", "equipment": "body weight", "target": "abs", "gif_url": ""},
        ],
    }
    for key, exercises in fallbacks.items():
        if key in muscle_zh:
            return exercises
    return fallbacks["腿"]