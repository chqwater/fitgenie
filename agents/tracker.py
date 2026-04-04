from datetime import date
from state import FitGenieState


def tracker_agent(state: FitGenieState) -> dict:
    """
    API 模式：直接从 State 读取 daily_log，不做 CLI 输入。
    daily_log 由 API 路由层在调用 graph.invoke 前注入。
    """
    print("\n[Tracker] 采集今日数据...")

    daily_log = state.get("daily_log")

    # 如果 daily_log 已经有数据（API 模式），直接用
    if daily_log and daily_log.get("date"):
        print(f"[Tracker] ✅ {daily_log}")
        return {"daily_log": daily_log}

    # 降级：CLI 模式（直接运行 main.py 时）
    daily_log = {
        "date": str(date.today()),
        "weight_kg": state["user_profile"]["weight_kg"],
        "steps": 8000,
        "calories_intake": 2000,
        "workout_done": True,
        "mood": "neutral",
    }
    print(f"[Tracker] ✅ {daily_log}")
    return {"daily_log": daily_log}