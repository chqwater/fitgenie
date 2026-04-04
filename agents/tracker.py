from datetime import date
from state import FitGenieState


def tracker_agent(state: FitGenieState) -> dict:
    print("\n[Tracker] 请输入今日数据")
    print("-" * 34)

    weight = _ask_float("体重 (kg)", state["user_profile"]["weight_kg"])
    steps = _ask_int("步数", 8000)
    calories = _ask_int("饮食热量 (kcal)", 2000)
    workout_done = _ask_bool("完成训练? (y/n)", True)
    mood = _ask_mood()

    daily_log = {
        "date": str(date.today()),
        "weight_kg": weight,
        "steps": steps,
        "calories_intake": calories,
        "workout_done": workout_done,
        "mood": mood,
    }

    # 同步更新用户档案中的体重
    from user_profile import update_profile_weight
    update_profile_weight(daily_log["weight_kg"])

    print(f"[Tracker] ✅ {daily_log}")
    return {"daily_log": daily_log}


def _ask_float(label: str, default: float) -> float:
    raw = input(f"  {label} (默认 {default}): ").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        print(f"  输入无效，使用默认值 {default}")
        return default


def _ask_int(label: str, default: int) -> int:
    raw = input(f"  {label} (默认 {default}): ").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"  输入无效，使用默认值 {default}")
        return default


def _ask_bool(label: str, default: bool) -> bool:
    raw = input(f"  {label}: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes", "1", "是")


def _ask_mood() -> str:
    options = {"1": "good", "2": "neutral", "3": "tired"}
    print("  情绪: 1=好  2=一般  3=疲惫")
    raw = input("  选择 (默认 2): ").strip()
    return options.get(raw, "neutral")