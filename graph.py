from langgraph.graph import StateGraph, END
from state import FitGenieState
from agents.tracker import tracker_agent
from agents.analyst import analyst_agent
from agents.coach import coach_agent
from agents.diet import diet_agent
from agents.mental import mental_agent
from memory.store import save_daily_log


def orchestrator_node(state: FitGenieState) -> dict:
    print("\n[Orchestrator] 仲裁决策...")

    plateau = state.get("plateau_detected", False)
    mood = state.get("daily_log", {}).get("mood", "neutral")
    conflict = plateau and mood == "tired"

    if conflict:
        mode = "conservative"
        print("[Orchestrator] 冲突：停滞 + 疲惫 → conservative")
    elif plateau:
        mode = "aggressive"
        print("[Orchestrator] 停滞 → aggressive")
    else:
        mode = "normal"
        print("[Orchestrator] 正常 → normal")

    return {
        "conflict_flag": conflict,
        "adjustment_mode": mode,
    }


def coach_and_diet_node(state: FitGenieState) -> dict:
    coach_result = coach_agent(state)
    diet_result = diet_agent(state)
    return {**coach_result, **diet_result}


def finalize_node(state: FitGenieState) -> dict:
    print("\n[Finalize] 生成今日总结...")

    from memory.store import save_workout_log

    user_id = state["user_id"]

    if state.get("daily_log"):
        save_daily_log(state["daily_log"], user_id=user_id)
        # 存入向量记忆
        from memory.vector_store import save_strategy
        save_strategy(user_id, state)

    muscle_group = state.get("_today_muscle_group", "全身")
    workout_plan = state.get("workout_plan", "")
    if workout_plan and state.get("daily_log"):
        save_workout_log(
            user_id=user_id,
            date_str=state["daily_log"]["date"],
            muscle_group=muscle_group,
            exercises=workout_plan,
        )

    summary = f"""
╔══════════════════════════════════╗
  FitGenie · {state['daily_log']['date']}
  模式：{state.get('adjustment_mode', 'normal').upper()}
╚══════════════════════════════════╝

【训练计划】
{state.get('workout_plan', '暂无')}

【饮食方案】
{state.get('diet_plan', '暂无')}

【趋势分析】
{state.get('trend_summary', '暂无')}

【教练寄语】
{state.get('motivation_message', '继续加油！')}
""".strip()

    print(summary)
    return {"final_summary": summary}


def build_graph():
    g = StateGraph(FitGenieState)

    g.add_node("tracker",     tracker_agent)
    g.add_node("analyst",     analyst_agent)
    g.add_node("orchestrate", orchestrator_node)
    g.add_node("plan",        coach_and_diet_node)
    g.add_node("mental",      mental_agent)
    g.add_node("finalize",    finalize_node)

    g.set_entry_point("tracker")
    g.add_edge("tracker",     "analyst")
    g.add_edge("analyst",     "orchestrate")
    g.add_edge("orchestrate", "plan")
    g.add_edge("plan",        "mental")
    g.add_edge("mental",      "finalize")
    g.add_edge("finalize",    END)

    return g.compile()


fitgenie_graph = build_graph()