# api/schemas.py
from pydantic import BaseModel, Field
from typing import Optional


# ── 认证 ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=30)
    password: str = Field(..., min_length=6, max_length=72)
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=10, le=100)
    weight_kg: float = Field(..., ge=30, le=300)
    height_cm: float = Field(..., ge=100, le=250)
    goal: str = Field(..., pattern="^(lose_fat|build_muscle|maintain)$")
    activity_level: str = Field(..., pattern="^(sedentary|light|moderate|active)$")
    dietary_pref: str = Field(..., pattern="^(no restriction|vegetarian|vegan|low_carb)$")


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── 每日打卡 ──────────────────────────────────────────────

class CheckinRequest(BaseModel):
    weight_kg: float = Field(..., ge=30, le=300)
    steps: int = Field(..., ge=0, le=100000)
    calories_intake: int = Field(..., ge=0, le=10000)
    workout_done: bool
    mood: str = Field(..., pattern="^(good|neutral|tired)$")


class CheckinResponse(BaseModel):
    date: str
    mode: str                  # normal / conservative / aggressive
    workout_plan: str
    diet_plan: str
    trend_summary: str
    motivation_message: str


# ── 历史记录 ──────────────────────────────────────────────

class DailyLogItem(BaseModel):
    date: str
    weight_kg: Optional[float]
    steps: Optional[int]
    calories_intake: Optional[int]
    workout_done: Optional[bool]
    mood: Optional[str]


# ── 用户档案 ──────────────────────────────────────────────

class ProfileResponse(BaseModel):
    name: str
    age: int
    weight_kg: float
    height_cm: float
    goal: str
    activity_level: str
    dietary_pref: str


class ProfileUpdateRequest(BaseModel):
    weight_kg: Optional[float] = Field(None, ge=30, le=300)
    goal: Optional[str] = Field(None, pattern="^(lose_fat|build_muscle|maintain)$")
    activity_level: Optional[str] = Field(None, pattern="^(sedentary|light|moderate|active)$")
    dietary_pref: Optional[str] = Field(None, pattern="^(no restriction|vegetarian|vegan|low_carb)$")