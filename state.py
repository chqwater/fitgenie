from typing import TypedDict, Optional


class UserProfile(TypedDict):
    id: int
    username: str
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


class AssistantDirectives(TypedDict, total=False):
    """小助手向各 Agent 传递的结构化指令"""
    mode: Optional[str]          # conservative / normal / aggressive / None
    workout_focus: str           # 希望侧重的训练内容
    workout_avoid: str           # 需要避免的动作/肌群
    diet_adjustments: str        # 饮食调整要求
    general_notes: str           # 其他注意事项


class FitGenieState(TypedDict):
    user_id: int
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
    # 小助手扩展字段
    assistant_directives: Optional[AssistantDirectives]  # 小助手传入的个性化指令
    user_preferences: Optional[dict]                     # 用户长期偏好画像