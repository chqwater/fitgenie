from state import FitGenieState
from memory.store import get_recent_weights
from llm_client import get_client


def analyst_agent(state: FitGenieState) -> dict:
    client = get_client()
    print("\n[Analyst] 分析近期趋势...")

    user_id = state["user_id"]
    recent_weights = get_recent_weights(user_id=user_id, days=7)
    plateau = _detect_plateau(recent_weights)
    trend_summary = _generate_trend_summary(client, recent_weights, plateau)
    suggestion = "增加热量缺口或调整训练强度" if plateau else "当前方案有效，保持执行"

    print(f"[Analyst] 停滞: {plateau} | 建议: {suggestion}")
    return {
        "plateau_detected": plateau,
        "trend_summary": trend_summary,
        "analyst_suggestion": suggestion,
    }


def _detect_plateau(weights: list[float]) -> bool:
    if len(weights) < 3:
        return False
    change = abs(weights[-1] - weights[0])
    return change < 0.2


def _generate_trend_summary(client, weights: list[float], plateau: bool) -> str:
    if not weights:
        return "数据不足，暂无趋势分析。"

    # 把 list 格式化成可读字符串，不暴露内部数据结构
    weight_str = " → ".join(str(w) for w in weights)

    prompt = f"""你是一位运动科学分析师。
近{len(weights)}天体重变化：{weight_str} (kg)
是否停滞：{"是" if plateau else "否"}
请用2-3句话总结趋势，不要在回复中出现任何列表格式或括号，用自然语言描述，用中文。"""

    response = client.chat.completions.create(
        model="hunyuan-lite",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()