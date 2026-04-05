from dotenv import load_dotenv
load_dotenv()

from memory.store import init_db, get_user_by_id
from graph import fitgenie_graph


def main():
    init_db()

    # CLI 模式默认用 user_id=1
    user = get_user_by_id(1)
    if not user:
        print("❌ 数据库里没有用户，请先通过前端注册")
        return

    print(f"\n[Profile] 欢迎回来，{user['name']} 👋")

    initial_state = {
        "user_id": user["id"],
        "user_profile": user,
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