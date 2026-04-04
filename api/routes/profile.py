# api/routes/profile.py
from fastapi import APIRouter, Depends, HTTPException
from api.auth import get_current_user_id
from api.schemas import ProfileResponse, ProfileUpdateRequest
from memory.store import get_user_by_id, update_user

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(user_id: int = Depends(get_current_user_id)):
    """获取当前用户档案"""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("", response_model=ProfileResponse)
def update_profile(
    body: ProfileUpdateRequest,
    user_id: int = Depends(get_current_user_id),
):
    """更新用户档案（只传要改的字段）"""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="没有要更新的字段")

    update_user(user_id, updates)
    return get_user_by_id(user_id)