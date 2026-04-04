from typing import TypedDict, Optional


class UserProfile(TypedDict):
    id: int                # 新增
    username: str          # 新增
    name: str
    age: int
    weight_kg: float
    height_cm: float
    goal: str
    activity_level: str
    dietary_pref: str


class DailyLog(TypedDict):
    date: str
    weight_kg: float
    steps: int
    calories_intake: int
    workout_done: bool
    mood: str


class FitGenieState(TypedDict):
    user_id: int           # 新增
    user_profile: UserProfile
    daily_log: DailyLog
    plateau_detected: bool
    trend_summary: str
    analyst_suggestion: str
    workout_plan: str
    diet_plan: str
    motivation_message: str
    conflict_flag: bool
    adjustment_mode: str
    final_summary: str