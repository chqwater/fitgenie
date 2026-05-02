import json
from langgraph.graph import StateGraph, END
from state import FitGenieState
from agents.tracker import tracker_agent
from agents.analyst import analyst_agent
from agents.coach import coach_agent
from agents.diet import diet_agent
from agents.mental import mental_agent
from memory.store import save_daily_log


def orchestrator_node(state: FitGenieState) -> dict:
    """
    标准 Orchestrator：基于停滞检测 + 情绪做模式仲裁。
    若 state 中已有小助手指令（assistant_directives），则直接采用助手的 mode 决策。
    """
    print("\n[Orchestrator] 仲裁决策...")

    directives = state.get("assistant_directives") or {}
    assistant_mode = directives.get("mode") if directives else None

    if assistant_mode:
        # 小助手已指定模式，跳过规则仲裁
        print(f"[Orchestrator] 小助手覆盖模式 → {assistant_mode}")
        return {
            "conflict_flag": False,
            "adjustment_mode": assistant_mode,
        }

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

    directives = state.get("assistant_directives") or {}
    mode_label = state.get('adjustment_mode', 'normal').upper()
    assistant_note = ""
    if directives:
        assistant_note = "\n  [小助手个性化定制]"

    summary = f"""
╔══════════════════════════════════╗
  FitGenie · {state['daily_log']['date']}
  模式：{mode_label}{assistant_note}
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


def build_regenerate_graph():
    """
    重新生成图：跳过 tracker（数据已存），直接从 analyst 开始。
    小助手指令会通过 orchestrator_node 传递给 coach/diet agent。
    """
    g = StateGraph(FitGenieState)

    g.add_node("analyst",     analyst_agent)
    g.add_node("orchestrate", orchestrator_node)
    g.add_node("plan",        coach_and_diet_node)
    g.add_node("mental",      mental_agent)
    g.add_node("finalize",    finalize_node)

    g.set_entry_point("analyst")
    g.add_edge("analyst",     "orchestrate")
    g.add_edge("orchestrate", "plan")
    g.add_edge("plan",        "mental")
    g.add_edge("mental",      "finalize")
    g.add_edge("finalize",    END)

    return g.compile()


fitgenie_graph = build_graph()
fitgenie_regenerate_graph = build_regenerate_graph()
