from state import FitGenieState
from llm_client import get_client
from memory.store import get_recent_workouts

INTENSITY = {
    "normal":       "保持当前训练量",
    "conservative": "今日减量训练，防止过度疲劳",
    "aggressive":   "适度增加训练强度，打破停滞",
}


def coach_agent(state: FitGenieState) -> dict:
    client = get_client()
    print("\n[Coach] 生成训练计划...")

    profile = state["user_profile"]
    mode = state.get("adjustment_mode", "normal")
    intensity_hint = INTENSITY.get(mode, "保持当前训练量")

    # ── 读取最近7天训练历史 ───────────────────────────────
    user_id = state["user_id"]
    recent_workouts = get_recent_workouts(user_id=user_id, days=7)
    history_context = _format_history(recent_workouts)

    prompt = f"""你是一位专业健身教练，请根据用户的训练历史生成今日训练计划。

    【用户信息】
    - 体重：{profile['weight_kg']}kg
    - 目标：{profile['goal']}
    - 活动水平：{profile['activity_level']}

    【最近7天训练记录】
    {history_context}

    【今日训练方向】
    {intensity_hint}

    【输出要求】
    只输出 JSON，不要有任何其他文字，格式如下：
    {{
      "type": "力量训练",
      "muscle_group": "胸/三头",
      "exercises": [
        {{"name": "哑铃卧推", "sets": 4, "reps": "10次"}},
        {{"name": "上斜飞鸟", "sets": 3, "reps": "12次"}}
      ],
      "calories_burned": 320,
      "duration_min": 50
    }}"""

    response = client.chat.completions.create(
        model="hunyuan-lite",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
    )
    raw = response.choices[0].message.content.strip()

    # 解析 JSON，失败时降级用原始文本
    from utils.formatter import parse_llm_json, format_workout
    data = parse_llm_json(raw)
    if data:
        plan = format_workout(data)
        muscle_group = data.get("muscle_group", "全身")
    else:
        # 降级：JSON 解析失败，用原始输出，不让系统崩溃
        print("[Coach] ⚠️ JSON 解析失败，使用原始输出")
        plan = raw
        muscle_group = _extract_muscle_group(raw)

    state["_today_muscle_group"] = muscle_group
    state["_today_exercises"] = plan

    print(f"[Coach] 今日肌群：{muscle_group}")
    return {"workout_plan": plan}


def _format_history(workouts: list[dict]) -> str:
    """把训练记录格式化成可读文本"""
    if not workouts:
        return "暂无训练记录（第一次训练，自由安排）"

    lines = []
    for w in workouts:
        lines.append(f"  {w['date']}：{w['muscle_group']}")
    return "\n".join(lines)


def _extract_muscle_group(plan: str) -> str:
    """
    从 LLM 输出里提取肌群名称。
    格式约定：第一行是"今日训练肌群：xxx"
    """
    for line in plan.split("\n"):
        if "训练肌群" in line and "：" in line:
            return line.split("：", 1)[1].strip()
    return "全身"