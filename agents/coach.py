from state import FitGenieState
from llm_client import get_client
from memory.store import get_recent_workouts
from tools.exercise_db import get_exercises_by_muscle

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

    # ── 读取训练历史 ──────────────────────────────────────
    recent_workouts = get_recent_workouts(user_id=state["user_id"], days=7)
    history_context = _format_history(recent_workouts)

    # ── 第一步：让 LLM 决定今天练什么肌群 ────────────────
    muscle_group = _decide_muscle_group(client, history_context, intensity_hint)
    print(f"[Coach] 今日肌群：{muscle_group}")

    # ── 第二步：调用 Tool 从真实数据库获取动作 ────────────
    print(f"[Coach] 🔧 调用 ExerciseDB 查询动作...")
    exercises = get_exercises_by_muscle(muscle_group, limit=6)
    exercise_list = _format_exercises(exercises)
    print(f"[Coach] ✅ 获取到 {len(exercises)} 个动作")

    # ── 第三步：让 LLM 从真实动作里选择并生成计划 ────────
    prompt = f"""你是一位专业健身教练，请根据以下真实动作库生成今日训练计划。

【今日目标肌群】{muscle_group}
【训练方向】{intensity_hint}
【用户体重】{profile['weight_kg']}kg

【可用动作库（来自 ExerciseDB）】
{exercise_list}

【输出要求】
只输出 JSON，格式如下：
{{
  "type": "力量训练",
  "muscle_group": "{muscle_group}",
  "exercises": [
    {{"name": "动作名", "sets": 4, "reps": "10次"}},
    {{"name": "动作名", "sets": 3, "reps": "12次"}}
  ],
  "calories_burned": 320,
  "duration_min": 50
}}

注意：exercises 只能从上面的可用动作库里选，不能自己发明动作。选3-5个。"""

    response = client.chat.completions.create(
        model="hunyuan-lite",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
    )
    raw = response.choices[0].message.content.strip()

    from utils.formatter import parse_llm_json, format_workout
    data = parse_llm_json(raw)
    if data:
        plan = format_workout(data)
    else:
        print("[Coach] ⚠️ JSON 解析失败，使用原始输出")
        plan = raw

    state["_today_muscle_group"] = muscle_group
    state["_today_exercises"] = plan

    return {"workout_plan": plan}


def _decide_muscle_group(client, history_context: str, intensity_hint: str) -> str:
    """
    第一步：让 LLM 根据训练历史决定今天练什么肌群。
    这是纯决策，不生成计划，token 消耗少。
    """
    prompt = f"""根据以下训练历史，决定今天应该训练哪个肌群。
遵循推拉腿分化原则，避免连续两天练同一肌群。

训练历史：
{history_context}

训练方向：{intensity_hint}

只输出肌群名称，例如：胸/三头、背/二头、腿/臀、肩/核心
不要输出其他任何内容。"""

    response = client.chat.completions.create(
        model="hunyuan-lite",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
    )
    return response.choices[0].message.content.strip()


def _format_history(workouts: list[dict]) -> str:
    if not workouts:
        return "暂无训练记录（第一次训练，自由安排）"
    return "\n".join(f"  {w['date']}：{w['muscle_group']}" for w in workouts)


def _format_exercises(exercises: list[dict]) -> str:
    """把动作列表格式化成 prompt 里的文字"""
    lines = []
    for i, ex in enumerate(exercises, 1):
        lines.append(f"  {i}. {ex['name_zh']} | 器械：{ex['equipment']}")
    return "\n".join(lines)


def _extract_muscle_group(plan: str) -> str:
    for line in plan.split("\n"):
        if "训练肌群" in line and "：" in line:
            return line.split("：", 1)[1].strip()
    return "全身"