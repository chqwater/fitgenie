# user_profile.py
# 用户注册 CLI + 数据验证

from memory.store import save_user, load_user, update_user_weight

# ── 合法值定义 ────────────────────────────────────────────

VALID_GOALS = {
    "1": "lose_fat",
    "2": "build_muscle",
    "3": "maintain",
}

VALID_ACTIVITY = {
    "1": "sedentary",
    "2": "light",
    "3": "moderate",
    "4": "active",
}

VALID_DIETARY = {
    "1": "no restriction",
    "2": "vegetarian",
    "3": "vegan",
    "4": "low_carb",
}


# ── 数据验证层 ────────────────────────────────────────────

class ValidationError(Exception):
    pass


def validate_profile(data: dict):
    """
    验证用户档案数据合法性。
    不合法时抛出 ValidationError，调用方决定怎么处理。
    """
    if not data.get("name") or len(data["name"].strip()) == 0:
        raise ValidationError("姓名不能为空")

    if not (10 <= data["age"] <= 100):
        raise ValidationError("年龄必须在 10–100 之间")

    if not (30 <= data["weight_kg"] <= 300):
        raise ValidationError("体重必须在 30–300 kg 之间")

    if not (100 <= data["height_cm"] <= 250):
        raise ValidationError("身高必须在 100–250 cm 之间")

    if data["goal"] not in VALID_GOALS.values():
        raise ValidationError(f"目标必须是: {list(VALID_GOALS.values())}")

    if data["activity_level"] not in VALID_ACTIVITY.values():
        raise ValidationError(f"活动水平必须是: {list(VALID_ACTIVITY.values())}")

    if data["dietary_pref"] not in VALID_DIETARY.values():
        raise ValidationError(f"饮食偏好必须是: {list(VALID_DIETARY.values())}")


# ── 注册 CLI ──────────────────────────────────────────────

def register_user() -> dict:
    """
    引导用户完成注册。
    验证失败时重新输入，不会崩溃。
    注册成功后存入数据库，返回 profile dict。
    """
    print("\n" + "=" * 42)
    print("  👤  首次使用，请创建你的档案")
    print("=" * 42)

    while True:
        try:
            profile = _collect_input()
            validate_profile(profile)
            user_id = save_user(profile)
            print(f"\n[Profile] ✅ 档案创建成功 (id={user_id})")
            _print_profile(profile)
            return profile

        except ValidationError as e:
            print(f"\n[Profile] ❌ 输入有误：{e}，请重新填写\n")


def _collect_input() -> dict:
    """收集用户输入，直接返回 dict，不做验证"""
    print()
    name = input("  姓名: ").strip()

    age = _ask_int("年龄")
    weight_kg = _ask_float("当前体重 (kg)")
    height_cm = _ask_float("身高 (cm)")

    print("\n  目标: 1=减脂  2=增肌  3=维持体重")
    goal = VALID_GOALS.get(input("  选择 (1/2/3): ").strip(), "lose_fat")

    print("\n  活动水平: 1=久坐  2=轻度  3=中度  4=高强度")
    activity = VALID_ACTIVITY.get(input("  选择 (1/2/3/4): ").strip(), "moderate")

    print("\n  饮食偏好: 1=无限制  2=素食  3=纯素  4=低碳")
    dietary = VALID_DIETARY.get(input("  选择 (1/2/3/4): ").strip(), "no restriction")

    return {
        "name": name,
        "age": age,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "goal": goal,
        "activity_level": activity,
        "dietary_pref": dietary,
    }


# ── 更新档案 ──────────────────────────────────────────────

def update_profile_weight(weight_kg: float):
    """Tracker 记录新体重后调用，同步更新用户档案"""
    update_user_weight(weight_kg)


# ── 辅助函数 ──────────────────────────────────────────────

def _ask_int(label: str) -> int:
    while True:
        try:
            return int(input(f"  {label}: ").strip())
        except ValueError:
            print(f"  请输入整数")


def _ask_float(label: str) -> float:
    while True:
        try:
            return float(input(f"  {label}: ").strip())
        except ValueError:
            print(f"  请输入数字")


def _print_profile(p: dict):
    print(f"""
  姓名：{p['name']}
  年龄：{p['age']} 岁
  体重：{p['weight_kg']} kg  身高：{p['height_cm']} cm
  目标：{p['goal']}
  活动：{p['activity_level']}
  饮食：{p['dietary_pref']}""")