# api/routes/assistant.py
from fastapi import APIRouter, Depends
from api.auth import get_current_user_id
from api.schemas import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantDirectives,
    AssistantHistoryItem,
)
from agents.assistant import chat as assistant_chat, get_preferences
from memory.store import get_assistant_history

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantChatResponse)
def chat(
    body: AssistantChatRequest,
    user_id: int = Depends(get_current_user_id),
):
    """与小助手对话。current_plan 可传入当日计划上下文。"""
    context = {"current_plan": body.current_plan} if body.current_plan else None
    result = assistant_chat(user_id=user_id, user_message=body.message, context=context)

    directives = None
    if result.get("directives"):
        directives = AssistantDirectives(**result["directives"])

    return AssistantChatResponse(
        reply=result["reply"],
        directives=directives,
        preferences_updated=result["preferences_updated"],
    )


@router.get("/history", response_model=list[AssistantHistoryItem])
def history(
    limit: int = 20,
    user_id: int = Depends(get_current_user_id),
):
    """获取与小助手的对话历史"""
    return get_assistant_history(user_id=user_id, limit=limit)


@router.get("/preferences")
def preferences(user_id: int = Depends(get_current_user_id)):
    """获取小助手记录的用户偏好"""
    return get_preferences(user_id=user_id)
