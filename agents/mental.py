from state import FitGenieState
from memory.store import get_streak
from llm_client import get_client


def mental_agent(state: FitGenieState) -> dict:
    client = get_client()
    print("\n[Mental] 生成激励反馈...")

    log = state.get("daily_log", {})
    plateau = state.get("plateau_detected", False)
    workout_done = log.get("workout_done", False)
    mood = log.get("mood", "neutral")
    user_id = state["user_id"]
    streak = get_streak(user_id=user_id)

    style = _decide_style(workout_done, mood, plateau, streak)

    prompt = f"""你是一位温暖专业的健身教练助手，请给用户一条激励消息。

用户今日状态：
- 完成训练：{"是" if workout_done else "否"}
- 情绪：{mood}
- 连续打卡：{streak}天
- 处于停滞期：{"是" if plateau else "否"}

激励风格：{style}

要求：2-3句话，口语化，真诚，不要过度鸡汤，用中文。"""

    response = client.chat.completions.create(
        model="hunyuan-lite",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
    )
    message = response.choices[0].message.content.strip()
    print(f"[Mental] 消息生成完成")
    return {"motivation_message": message}


def _decide_style(
    workout_done: bool,
    mood: str,
    plateau: bool,
    streak: int
) -> str:
    if not workout_done and mood == "tired":
        return "温柔理解，今天休息也没关系，明天继续"
    if plateau:
        return "科学解释停滞原因，给予信心，不要急躁"
    if streak >= 7:
        return "肯定连续坚持的成就感，鼓励保持势头"
    if workout_done:
        return "肯定今日完成，激励保持连续性"
    return "轻松鼓励，提示明天计划"