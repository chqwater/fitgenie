# memory/vector_store.py
# ─────────────────────────────────────────────────────────────────────────────
# 向量记忆层
# 存储：每次 daily loop 结束后，把"情境+策略+结果"打包成文字存入 Chroma
# 召回：Analyst 运行时，用当前情境查询最相似的历史案例
# ─────────────────────────────────────────────────────────────────────────────

import os
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from llm_client import get_client

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")


class HunyuanEmbeddingFunction(EmbeddingFunction):
    """用混元 API 生成 embedding，替代本地 sentence-transformers"""

    def __call__(self, input: Documents) -> Embeddings:
        client = get_client()
        embeddings = []
        for text in input:
            try:
                response = client.embeddings.create(
                    model="text-embedding-ada-002",  # 混元兼容 OpenAI embedding
                    input=text,
                )
                embeddings.append(response.data[0].embedding)
            except Exception as e:
                print(f"[Embedding] ⚠️ 生成失败: {e}，使用零向量")
                embeddings.append([0.0] * 1536)
        return embeddings


EMBEDDING_FN = HunyuanEmbeddingFunction()


def _get_collection(user_id: int):
    """获取用户专属的 Chroma collection"""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(
        name=f"user_{user_id}_strategies",
        embedding_function=EMBEDDING_FN,
        metadata={"hnsw:space": "cosine"},  # 余弦相似度
    )


def save_strategy(user_id: int, state: dict):
    """
    每次 daily loop 结束后调用。
    把情境 + 策略存入向量库。
    """
    daily_log = state.get("daily_log", {})
    if not daily_log.get("date"):
        return

    # ── 构建情境描述文字 ────────────────────────────────────
    # 这段文字会被转成向量，所以要尽量包含关键信息
    context_text = f"""
日期：{daily_log.get('date')}
体重：{daily_log.get('weight_kg')}kg
步数：{daily_log.get('steps')}
热量摄入：{daily_log.get('calories_intake')}kcal
完成训练：{'是' if daily_log.get('workout_done') else '否'}
情绪：{daily_log.get('mood')}
是否停滞：{'是' if state.get('plateau_detected') else '否'}
趋势：{state.get('trend_summary', '')}
""".strip()

    # ── 构建策略描述文字 ────────────────────────────────────
    strategy_text = f"""
调整模式：{state.get('adjustment_mode', 'normal')}
训练计划：{state.get('workout_plan', '')[:200]}
饮食方案：{state.get('diet_plan', '')[:200]}
""".strip()

    # ── 存入 Chroma ──────────────────────────────────────────
    collection = _get_collection(user_id)
    doc_id = f"{user_id}_{daily_log['date']}"

    try:
        collection.upsert(
            ids=[doc_id],
            documents=[context_text],           # 用情境文字生成向量
            metadatas=[{
                "date": daily_log["date"],
                "mode": state.get("adjustment_mode", "normal"),
                "plateau": str(state.get("plateau_detected", False)),
                "mood": daily_log.get("mood", "neutral"),
                "strategy": strategy_text,       # 策略存在 metadata 里
            }],
        )
        print(f"[VectorStore] 💾 策略已存储: {daily_log['date']}")
    except Exception as e:
        print(f"[VectorStore] ⚠️ 存储失败: {e}")


def recall_similar_strategy(user_id: int, current_context: str, n_results: int = 2) -> list[dict]:
    """
    用当前情境查询最相似的历史案例。
    返回最相似的 N 条历史策略。
    """
    collection = _get_collection(user_id)

    try:
        # 检查是否有足够数据
        if collection.count() == 0:
            return []

        results = collection.query(
            query_texts=[current_context],
            n_results=min(n_results, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        recalled = []
        for i, metadata in enumerate(results["metadatas"][0]):
            distance = results["distances"][0][i]
            similarity = 1 - distance  # 余弦距离转相似度

            # 只返回相似度足够高的结果
            if similarity > 0.5:
                recalled.append({
                    "date": metadata["date"],
                    "mode": metadata["mode"],
                    "mood": metadata["mood"],
                    "plateau": metadata["plateau"],
                    "strategy": metadata["strategy"],
                    "similarity": round(similarity, 3),
                })

        return recalled

    except Exception as e:
        print(f"[VectorStore] ⚠️ 召回失败: {e}")
        return []


def build_context_text(state: dict) -> str:
    """
    把当前 State 转成情境描述文字，用于向量查询。
    和 save_strategy 里的格式保持一致。
    """
    daily_log = state.get("daily_log", {})
    return f"""
体重：{daily_log.get('weight_kg')}kg
情绪：{daily_log.get('mood')}
是否停滞：{'是' if state.get('plateau_detected') else '否'}
趋势：{state.get('trend_summary', '')}
""".strip()