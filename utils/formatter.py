# utils/formatter.py
# 把 LLM 输出的 JSON 格式化成用户可读的文字
import json


def parse_llm_json(raw: str) -> dict | None:
    """
    从 LLM 输出里提取 JSON。
    LLM 有时会在 JSON 前后加说明文字或 markdown 代码块，需要清理。
    """
    # 去掉 markdown 代码块标记
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        # 去掉第一行(```json)和最后一行(```)
        raw = "\n".join(lines[1:-1])

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # JSON 解析失败，返回 None，调用方降级处理
        return None


def format_workout(data: dict) -> str:
    """把训练计划 JSON 格式化成可读文字"""
    if not data:
        return "训练计划生成失败"

    lines = []
    lines.append(f"训练类型：{data.get('type', '未知')}")
    lines.append(f"目标肌群：{data.get('muscle_group', '未知')}")
    lines.append("")
    lines.append("动作清单：")

    for i, ex in enumerate(data.get("exercises", []), 1):
        lines.append(f"  {i}. {ex['name']} — {ex['sets']}组 × {ex['reps']}")

    lines.append("")
    lines.append(f"预计消耗：{data.get('calories_burned', '?')} kcal")
    lines.append(f"训练时长：约{data.get('duration_min', '?')}分钟")

    return "\n".join(lines)


def format_diet(data: dict) -> str:
    """把饮食方案 JSON 格式化成可读文字"""
    if not data:
        return "饮食方案生成失败"

    lines = []
    lines.append(f"目标热量：{data.get('target_kcal', '?')} kcal")
    lines.append("")

    meals = data.get("meals", {})
    for meal_name, meal in meals.items():
        lines.append(f"【{meal_name}】{meal.get('kcal', '?')} kcal")
        for item in meal.get("items", []):
            lines.append(f"  · {item}")
        lines.append("")

    macro = data.get("macros", {})
    lines.append(
        f"宏量：蛋白质 {macro.get('protein_g', '?')}g｜"
        f"碳水 {macro.get('carb_g', '?')}g｜"
        f"脂肪 {macro.get('fat_g', '?')}g"
    )

    return "\n".join(lines)