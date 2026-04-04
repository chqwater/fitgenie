from state import FitGenieState
from llm_client import get_client


ACTIVITY_MULTIPLIER = {
    "sedentary": 1.2,
    "light":     1.375,
    "moderate":  1.55,
    "active":    1.725,
}

DEFICIT = {
    "normal":       400,
    "conservative": 200,
    "aggressive":   600,
}


def diet_agent(state: FitGenieState) -> dict:
    client = get_client()
    print("\n[Diet] 生成饮食方案...")

    profile = state["user_profile"]
    mode = state.get("adjustment_mode", "normal")

    bmr = _calc_bmr(profile)
    tdee = round(bmr * ACTIVITY_MULTIPLIER.get(profile["activity_level"], 1.55))
    deficit = DEFICIT.get(mode, 400)
    target = tdee - deficit

    protein_g = round(profile['weight_kg'] * 2.2)
    fat_g = round(target * 0.25 / 9)
    carb_g = round((target - protein_g * 4 - fat_g * 9) / 4)

    prompt = f"""你是一位注册营养师，请生成今日饮食方案。

    【必须遵守的参数】
    - 目标热量：{target} kcal
    - 蛋白质：{protein_g}g
    - 脂肪：{fat_g}g
    - 碳水化合物：{carb_g}g
    - 饮食偏好：{profile['dietary_pref']}

    【输出要求】
    只输出 JSON，不要有任何其他文字，格式如下：
    {{
      "target_kcal": {target},
      "meals": {{
        "早餐": {{
          "kcal": 600,
          "items": ["燕麦粥 50g", "鸡蛋 2个"]
        }},
        "午餐": {{
          "kcal": 900,
          "items": ["鸡胸肉 150g", "糙米 100g", "西兰花 200g"]
        }},
        "晚餐": {{
          "kcal": 700,
          "items": ["三文鱼 150g", "红薯 100g"]
        }}
      }},
      "macros": {{
        "protein_g": {protein_g},
        "carb_g": {carb_g},
        "fat_g": {fat_g}
      }}
    }}"""

    response = client.chat.completions.create(
        model="hunyuan-lite",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    raw = response.choices[0].message.content.strip()

    from utils.formatter import parse_llm_json, format_diet
    data = parse_llm_json(raw)
    if data:
        plan = format_diet(data)
    else:
        print("[Diet] ⚠️ JSON 解析失败，使用原始输出")
        plan = raw

    print(f"[Diet] 目标热量 {target} kcal")
    return {"diet_plan": plan}


def _calc_bmr(profile: dict) -> float:
    w = profile["weight_kg"]
    h = profile["height_cm"]
    a = profile["age"]
    return 10 * w + 6.25 * h - 5 * a + 5