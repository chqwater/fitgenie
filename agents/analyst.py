from state import FitGenieState
from memory.store import get_recent_weights
from memory.vector_store import recall_similar_strategy, build_context_text
from llm_client import get_client


def analyst_agent(state: FitGenieState) -> dict:
    client = get_client()
    print("\n[Analyst] 分析近期趋势...")

    user_id = state["user_id"]
    recent_weights = get_recent_weights(user_id=user_id, days=7)
    plateau = _detect_plateau(recent_weights)

    # ── 向量记忆召回 ──────────────────────────────────────
    current_context = build_context_text({
        **state,
        "plateau_detected": plateau,
    })
    recalled = recall_similar_strategy(user_id, current_context, n_results=2)

    if recalled:
        print(f"[Analyst] 🧠 召回 {len(recalled)} 条相似历史策略")
        for r in recalled:
            print(f"  → {r['date']} 相似度:{r['similarity']} 模式:{r['mode']}")
    else:
        print("[Analyst] 🧠 暂无相似历史，首次建立记忆")

    # ── 生成趋势总结（注入历史策略）─────────────────────
    trend_summary = _generate_trend_summary(
        client, recent_weights, plateau, recalled
    )

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


def _generate_trend_summary(
    client,
    weights: list[float],
    plateau: bool,
    recalled: list[dict]
) -> str:
    if not weights:
        return "数据不足，暂无趋势分析。"

    weight_str = " → ".join(str(w) for w in weights)

    # 把历史策略注入 prompt
    history_hint = ""
    if recalled:
        history_hint = "\n\n【相似历史参考】\n"
        for r in recalled:
            history_hint += f"- {r['date']}（相似度{r['similarity']}）：{r['mode']} 模式，{r['strategy'][:100]}\n"

    prompt = f"""你是一位运动科学分析师。
近{len(weights)}天体重变化：{weight_str} (kg)
是否停滞：{"是" if plateau else "否"}
{history_hint}
请用2-3句话总结趋势，如果有历史参考请提及上次类似情况的处理效果。
不要出现列表或括号，用自然语言，用中文。"""

    response = client.chat.completions.create(
        model="hunyuan-lite",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()