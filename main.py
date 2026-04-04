from dotenv import load_dotenv
load_dotenv()

from memory.store import init_db, load_user
from user_profile import register_user
from graph import fitgenie_graph


def main():
    init_db()

    # ── 检测用户档案 ──────────────────────────────────────
    user_profile = load_user()

    if user_profile is None:
        # 首次启动，引导注册
        user_profile = register_user()
    else:
        print(f"\n[Profile] 欢迎回来，{user_profile['name']} 👋")

    # ── 构建初始 State ────────────────────────────────────
    initial_state = {
        "user_profile": user_profile,
        "daily_log": {},
        "plateau_detected": False,
        "trend_summary": "",
        "analyst_suggestion": "",
        "workout_plan": "",
        "diet_plan": "",
        "motivation_message": "",
        "conflict_flag": False,
        "adjustment_mode": "normal",
        "final_summary": "",
    }

    print("\n" + "=" * 42)
    print("  🏋️  FitGenie Daily Loop Starting...")
    print("=" * 42)

    fitgenie_graph.invoke(initial_state)

    print("\n" + "=" * 42)
    print("  ✅  Daily Loop Complete")
    print("=" * 42)


if __name__ == "__main__":
    main()