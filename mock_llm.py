import random


TREND_RESPONSES = [
    "近7天体重从78.0kg下降至77.3kg，平均每天减少约0.1kg，减脂进度良好，建议保持当前方案。",
    "体重整体向下但近3天趋于平稳，可能进入短暂平台期，建议再观察3天再调整。",
    "近一周体重下降0.6kg，步数和热量控制均在目标范围内，继续执行当前计划。",
]

WORKOUT_RESPONSES = [
    """训练类型：力量训练（推胸）
动作：
1. 哑铃卧推 4组×10次
2. 上斜飞鸟 3组×12次
3. 三头绳索下压 3组×12次
预计消耗：300 kcal""",

    """训练类型：HIIT
动作：
1. 波比跳 4组×10次
2. 开合跳 4组×40秒
3. 平板支撑 3组×45秒
预计消耗：380 kcal""",

    """训练类型：主动恢复
动作：
1. 慢跑30分钟
2. 全身拉伸15分钟
预计消耗：180 kcal""",
]

DIET_RESPONSES = [
    """目标热量：1850 kcal
三餐：早餐500 / 午餐750 / 晚餐600
宏量：蛋白质160g / 碳水170g / 脂肪59g
推荐食材：鸡胸肉、糙米、西兰花""",

    """目标热量：1950 kcal
三餐：早餐450 / 午餐800 / 晚餐700
宏量：蛋白质155g / 碳水190g / 脂肪64g
推荐食材：三文鱼、藜麦、牛油果""",
]

MENTAL_RESPONSES = [
    "今天完成训练了，很好。坚持是最难的事，你已经在做了。",
    "停滞期是正常的生理反应，不是你的问题。保持节奏，突破就在前面。",
    "感觉累很正常，今天能动一动就已经赢了。长期一致性才是关键。",
    "数据在往好的方向走。把今天的状态保持下去。",
]


class _Message:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Message(content)


class _Completion:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class _Completions:
    def create(self, model="", messages=None, max_tokens=300, **kwargs):
        prompt = str(messages)

        if "教练助手" in prompt:
            reply = random.choice(MENTAL_RESPONSES)
        elif "趋势" in prompt or "体重记录" in prompt:
            reply = random.choice(TREND_RESPONSES)
        elif "健身教练" in prompt:
            reply = random.choice(WORKOUT_RESPONSES)
        elif "营养师" in prompt:
            reply = random.choice(DIET_RESPONSES)
        else:
            reply = "好的，继续保持当前计划。"

        return _Completion(reply)


class _Chat:
    def __init__(self):
        self.completions = _Completions()


class MockOpenAI:
    def __init__(self, **kwargs):
        self.chat = _Chat()