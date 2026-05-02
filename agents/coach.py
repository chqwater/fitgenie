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

    # 小助手指令
    directives = state.get("assistant_directives") or {}
    user_preferences = state.get("user_preferences") or {}
    if directives:
        print(f"[Coach] 🎯 收到小助手指令: {directives}")
    directive_hint = _build_directive_hint(directives, user_preferences)

    # ── 读取训练历史 ──────────────────────────────────────
    recent_workouts = get_recent_workouts(user_id=state["user_id"], days=7)
    history_context = _format_history(recent_workouts)

    # ── 第一步：让 LLM 决定今天练什么肌群 ────────────────
    muscle_group = _decide_muscle_group(client, history_context, intensity_hint, directives)
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
{directive_hint}
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


def _build_directive_hint(directives: dict, user_preferences: dict) -> str:
    lines = []
    if directives.get("workout_focus"):
        lines.append(f"【用户特别要求-侧重】{directives['workout_focus']}")
    if directives.get("workout_avoid"):
        lines.append(f"【用户特别要求-避免】{directives['workout_avoid']}")
    if directives.get("general_notes"):
        lines.append(f"【用户备注】{directives['general_notes']}")
    if user_preferences.get("workout_dislikes"):
        lines.append(f"【用户长期偏好-避免动作】{user_preferences['workout_dislikes']}")
    if user_preferences.get("injury_notes"):
        lines.append(f"【用户身体状况】{user_preferences['injury_notes']}")
    return "\n".join(lines) + "\n" if lines else ""


_AVOID_KEYWORDS = {
    "腿": ["腿/臀", "腿"],
    "臀": ["腿/臀"],
    "胸": ["胸/三头", "胸"],
    "背": ["背/二头", "背"],
    "肩": ["肩/核心", "肩"],
    "二头": ["背/二头"],
    "三头": ["胸/三头"],
    "核心": ["肩/核心"],
}

ALL_GROUPS = ["胸/三头", "背/二头", "腿/臀", "肩/核心"]


def _avoided_groups(avoid_text: str) -> set[str]:
    """从用户的 avoid 描述中解析出要禁止的肌群名"""
    if not avoid_text:
        return set()
    result = set()
    for keyword, groups in _AVOID_KEYWORDS.items():
        if keyword in avoid_text:
            result.update(groups)
    return result


def _decide_muscle_group(client, history_context: str, intensity_hint: str, directives: dict = None) -> str:
    """
    第一步：让 LLM 根据训练历史决定今天练什么肌群。
    """
    directives = directives or {}
    focus = directives.get("workout_focus") or ""
    avoid = directives.get("workout_avoid") or ""

    # 用户偏好里的长期 avoid 也合并进来
    avoided = _avoided_groups(avoid)

    extra_hint = ""
    if focus:
        extra_hint += f"\n【用户特别要求-侧重】{focus}"
    if avoid:
        avoided_str = "、".join(avoided) if avoided else avoid
        extra_hint += f"\n【用户特别要求-禁止】绝对不要选择：{avoided_str}（用户明确表示：{avoid}）"

    candidate_groups = [g for g in ALL_GROUPS if g not in avoided]
    if not candidate_groups:
        candidate_groups = ALL_GROUPS  # fallback：用户避免了所有，至少给一个

    options_str = "、".join(candidate_groups)

    prompt = f"""根据以下训练历史，决定今天应该训练哪个肌群。
遵循推拉腿分化原则，避免连续两天练同一肌群。

训练历史：
{history_context}

训练方向：{intensity_hint}{extra_hint}

只能从以下肌群中选择一个：{options_str}
只输出肌群名称，不要输出其他任何内容。"""

    response = client.chat.completions.create(
        model="hunyuan-lite",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
    )
    chosen = response.choices[0].message.content.strip()

    # 硬性兜底：如果 LLM 仍然选了被禁的肌群，强制换
    if chosen in avoided or chosen not in ALL_GROUPS:
        if candidate_groups:
            chosen = candidate_groups[0]
            print(f"[Coach] ⚠️ LLM 选择被禁/无效，强制改为：{chosen}")

    return chosen


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