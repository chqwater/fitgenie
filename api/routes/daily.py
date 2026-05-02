# api/routes/daily.py
from fastapi import APIRouter, Depends, HTTPException
from api.auth import get_current_user_id
from api.schemas import CheckinRequest, CheckinResponse, DailyLogItem, RegenerateRequest
from memory.store import get_user_by_id, get_recent_logs, get_user_preferences
from graph import fitgenie_graph, fitgenie_regenerate_graph

router = APIRouter(prefix="/daily", tags=["daily"])


@router.post("/checkin", response_model=CheckinResponse)
def checkin(
    body: CheckinRequest,
    user_id: int = Depends(get_current_user_id),
):
    """
    每日打卡：传入今日数据，触发 daily loop，返回今日方案。
    """
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 构建 State，注入用户数据和今日打卡
    from datetime import date
    initial_state = {
        "user_id": user_id,
        "user_profile": user,
        "daily_log": {
            "date": str(date.today()),
            "weight_kg": body.weight_kg,
            "steps": body.steps,
            "calories_intake": body.calories_intake,
            "workout_done": body.workout_done,
            "mood": body.mood,
        },
        "plateau_detected": False,
        "trend_summary": "",
        "analyst_suggestion": "",
        "workout_plan": "",
        "diet_plan": "",
        "motivation_message": "",
        "conflict_flag": False,
        "adjustment_mode": "normal",
        "final_summary": "",
    }

    final_state = fitgenie_graph.invoke(initial_state)

    return CheckinResponse(
        date=str(date.today()),
        mode=final_state["adjustment_mode"],
        workout_plan=final_state["workout_plan"],
        diet_plan=final_state["diet_plan"],
        trend_summary=final_state["trend_summary"],
        motivation_message=final_state["motivation_message"],
    )


@router.post("/regenerate", response_model=CheckinResponse)
def regenerate(
    body: RegenerateRequest,
    user_id: int = Depends(get_current_user_id),
):
    """
    重新生成今日方案。
    可携带小助手指令（directives）替代 orchestrator 的模式决策。
    跳过 tracker 节点，直接从 analyst 开始。
    """
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    from datetime import date
    directives_dict = None
    if body.directives:
        directives_dict = body.directives.model_dump(exclude_none=True)

    user_preferences = get_user_preferences(user_id)

    initial_state = {
        "user_id": user_id,
        "user_profile": user,
        "daily_log": {
            "date": str(date.today()),
            "weight_kg": body.weight_kg,
            "steps": body.steps,
            "calories_intake": body.calories_intake,
            "workout_done": body.workout_done,
            "mood": body.mood,
        },
        "plateau_detected": False,
        "trend_summary": "",
        "analyst_suggestion": "",
        "workout_plan": "",
        "diet_plan": "",
        "motivation_message": "",
        "conflict_flag": False,
        "adjustment_mode": "normal",
        "final_summary": "",
        "assistant_directives": directives_dict,
        "user_preferences": user_preferences,
    }

    final_state = fitgenie_regenerate_graph.invoke(initial_state)

    return CheckinResponse(
        date=str(date.today()),
        mode=final_state["adjustment_mode"],
        workout_plan=final_state["workout_plan"],
        diet_plan=final_state["diet_plan"],
        trend_summary=final_state["trend_summary"],
        motivation_message=final_state["motivation_message"],
    )


@router.get("/history", response_model=list[DailyLogItem])
def get_history(
    days: int = 7,
    user_id: int = Depends(get_current_user_id),
):
    """获取最近 N 天的打卡记录"""
    return get_recent_logs(user_id=user_id, days=days)