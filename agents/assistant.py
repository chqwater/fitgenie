"""
FitGenie 小助手 Agent

职责：
1. 随时与用户对话，记录偏好与用户画像
2. 当用户对计划不满意时，解析不满意原因并生成结构化指令
3. 在重新生成时替代 Orchestrator 的角色协调各 Agent
"""

import json
from llm_client import get_client
from memory.store import (
    save_assistant_message,
    get_assistant_history,
    get_user_preferences,
    save_user_preferences,
)


# ── 公开接口 ──────────────────────────────────────────────

def chat(user_id: int, user_message: str, context: dict | None = None) -> dict:
    """
    通用对话：用户随时可以和小助手说话。
    context 可以包含 current_plan（当日已生成的计划）。

    返回：
        {
          "reply": str,           # 助手回复
          "directives": dict,     # 提取到的结构化指令（若有）
          "preferences_updated": bool
        }
    """
    client = get_client()

    history = get_assistant_history(user_id, limit=16)
    preferences = get_user_preferences(user_id)

    # 保存用户消息
    save_assistant_message(user_id, "user", user_message)

    system_prompt = _build_system_prompt(preferences, context)

    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="hunyuan-turbo",
        messages=messages,
        max_tokens=600,
        temperature=0.7,
    )
    raw_reply = response.choices[0].message.content.strip()

    # 尝试解析 JSON 指令块（助手在回复末尾附加）
    reply_text, directives = _extract_directives(raw_reply)

    # 保存助手回复
    save_assistant_message(user_id, "assistant", reply_text)

    # 提取并更新用户偏好
    preferences_updated = False
    if directives or _has_preference_signals(user_message):
        updated_prefs = _extract_and_merge_preferences(
            client, user_message, reply_text, preferences
        )
        if updated_prefs != preferences:
            save_user_preferences(user_id, updated_prefs)
            preferences_updated = True

    return {
        "reply": reply_text,
        "directives": directives,
        "preferences_updated": preferences_updated,
    }


def get_preferences(user_id: int) -> dict:
    return get_user_preferences(user_id)


# ── 内部实现 ──────────────────────────────────────────────

def _build_system_prompt(preferences: dict, context: dict | None) -> str:
    pref_text = ""
    if preferences:
        pref_text = f"""
已知用户偏好：
{json.dumps(preferences, ensure_ascii=False, indent=2)}
"""

    plan_text = ""
    if context and context.get("current_plan"):
        plan = context["current_plan"]
        plan_text = f"""
当前已生成的计划：
- 模式：{plan.get('mode', '未知')}
- 训练计划：{plan.get('workout_plan', '暂无')[:300]}
- 饮食方案：{plan.get('diet_plan', '暂无')[:300]}
- 趋势分析：{plan.get('trend_summary', '暂无')[:200]}
"""

    return f"""你是 FitGenie 小助手，一位专业、贴心的 AI 健身教练助理。

你的职责：
1. 与用户随时对话，了解他们的健身偏好、习惯和诉求
2. 当用户对今日计划不满意时，理解原因并给出调整方向
3. 如果用户明确表达对计划的修改需求（如"训练太强了"、"想多练背"、"热量太少了"），
   在正常回复之后追加一个 JSON 指令块，格式如下：

<DIRECTIVES>
{{
  "mode": "conservative|normal|aggressive|null",
  "workout_focus": "...",
  "workout_avoid": "...",
  "diet_adjustments": "...",
  "general_notes": "..."
}}
</DIRECTIVES>

mode 说明：
- conservative：降低强度，保护恢复（适合疲劳/受伤/过度训练）
- aggressive：提升强度，突破停滞（适合长期无进展）
- normal：维持当前强度
- null：不改变 orchestrator 的决策

只在用户有明确计划修改需求时才输出 <DIRECTIVES> 块，普通聊天不输出。

{pref_text}
{plan_text}

回复风格：简洁专业，中文，有温度，不说废话。"""


def _extract_directives(raw_reply: str) -> tuple[str, dict]:
    """从助手回复中提取 <DIRECTIVES> JSON 块"""
    import re
    pattern = r"<DIRECTIVES>\s*([\s\S]*?)\s*</DIRECTIVES>"
    match = re.search(pattern, raw_reply)
    if not match:
        return raw_reply, {}

    reply_text = raw_reply[:match.start()].strip()
    json_str = match.group(1).strip()
    try:
        directives = json.loads(json_str)
        # 清理 null 字符串
        if directives.get("mode") in (None, "null", ""):
            directives["mode"] = None
        return reply_text, directives
    except json.JSONDecodeError:
        return reply_text, {}


def _has_preference_signals(message: str) -> bool:
    """检测消息是否包含偏好信号词"""
    signals = [
        "喜欢", "不喜欢", "讨厌", "偏好", "习惯", "不想", "想要",
        "过敏", "不吃", "素食", "低碳", "增肌", "减脂",
        "受伤", "膝盖", "腰", "肩膀", "背痛",
    ]
    return any(s in message for s in signals)


def _extract_and_merge_preferences(
    client, user_message: str, reply_text: str, existing_prefs: dict
) -> dict:
    """用 LLM 从对话中提取偏好并与现有偏好合并"""
    existing_str = json.dumps(existing_prefs, ensure_ascii=False) if existing_prefs else "{}"

    prompt = f"""从以下用户消息中提取健身偏好信息，与已有偏好合并，以 JSON 格式返回。
只返回 JSON，不要其他文字。

用户消息："{user_message}"
助手回复："{reply_text}"

现有偏好：{existing_str}

可提取的偏好类别（只提取有明确信息的字段）：
- workout_likes: 喜欢的训练类型
- workout_dislikes: 不喜欢/受伤避免的动作
- diet_restrictions: 饮食限制
- diet_preferences: 饮食喜好
- injury_notes: 受伤/身体状况备注
- schedule_notes: 训练时间/频率偏好
- goal_notes: 目标相关补充

返回合并后的 JSON（保留原有字段，新信息追加或覆盖）："""

    try:
        resp = client.chat.completions.create(
            model="hunyuan-lite",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        # 去掉 markdown 代码块
        raw = raw.strip("`").strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
        return json.loads(raw)
    except Exception:
        return existing_prefs
