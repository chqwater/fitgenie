# memory/vector_store.py
# 轻量向量记忆：用 SQLite 存策略文字，用 API embedding 做相似度搜索
# 不依赖 chromadb / torch / transformers，镜像体积不变

import os
import json
import sqlite3
import math
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "fitgenie.db")


# ── 初始化向量表 ──────────────────────────────────────────

def init_vector_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS strategy_vectors (
            id          TEXT PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            date        TEXT NOT NULL,
            context     TEXT NOT NULL,
            strategy    TEXT NOT NULL,
            mode        TEXT NOT NULL,
            embedding   TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ── 生成 Embedding ────────────────────────────────────────

def _get_embedding(text: str) -> list[float]:
    """调用混元 API 生成文字的向量表示"""
    try:
        from llm_client import get_client
        client = get_client()
        response = client.embeddings.create(
            model="text-embedding-v1",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"[VectorStore] ⚠️ Embedding 失败: {e}")
        return []


# ── 余弦相似度计算 ────────────────────────────────────────

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ── 存储策略 ──────────────────────────────────────────────

def save_strategy(user_id: int, state: dict):
    daily_log = state.get("daily_log", {})
    if not daily_log.get("date"):
        return

    context_text = f"""
体重：{daily_log.get('weight_kg')}kg
情绪：{daily_log.get('mood')}
完成训练：{'是' if daily_log.get('workout_done') else '否'}
是否停滞：{'是' if state.get('plateau_detected') else '否'}
趋势：{state.get('trend_summary', '')}
""".strip()

    strategy_text = f"""
调整模式：{state.get('adjustment_mode', 'normal')}
训练：{state.get('workout_plan', '')[:150]}
饮食：{state.get('diet_plan', '')[:150]}
""".strip()

    embedding = _get_embedding(context_text)
    if not embedding:
        print("[VectorStore] ⚠️ 无法生成 embedding，跳过存储")
        return

    doc_id = f"{user_id}_{daily_log['date']}"
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            INSERT OR REPLACE INTO strategy_vectors
                (id, user_id, date, context, strategy, mode, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id, user_id,
            daily_log["date"],
            context_text,
            strategy_text,
            state.get("adjustment_mode", "normal"),
            json.dumps(embedding),
        ))
        conn.commit()
        print(f"[VectorStore] 💾 策略已存储: {daily_log['date']}")
    except Exception as e:
        print(f"[VectorStore] ⚠️ 存储失败: {e}")
    finally:
        conn.close()


# ── 召回相似策略 ──────────────────────────────────────────

def recall_similar_strategy(user_id: int, current_context: str, n_results: int = 2) -> list[dict]:
    query_embedding = _get_embedding(current_context)
    if not query_embedding:
        return []

    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("""
            SELECT date, context, strategy, mode, embedding
            FROM strategy_vectors
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT 20
        """, (user_id,)).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    scored = []
    for row in rows:
        date_str, context, strategy, mode, emb_json = row
        emb = json.loads(emb_json)
        similarity = _cosine_similarity(query_embedding, emb)
        if similarity > 0.5:
            scored.append({
                "date": date_str,
                "mode": mode,
                "strategy": strategy,
                "similarity": round(similarity, 3),
            })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:n_results]


# ── 构建当前情境文字 ──────────────────────────────────────

def build_context_text(state: dict) -> str:
    daily_log = state.get("daily_log", {})
    return f"""
体重：{daily_log.get('weight_kg')}kg
情绪：{daily_log.get('mood')}
是否停滞：{'是' if state.get('plateau_detected') else '否'}
趋势：{state.get('trend_summary', '')}
""".strip()