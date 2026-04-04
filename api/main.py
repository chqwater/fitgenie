# api/main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from memory.store import init_db
from api.auth import auth_router
from api.routes.daily import router as daily_router
from api.routes.profile import router as profile_router

app = FastAPI(
    title="FitGenie API",
    description="Multi-Agent Personalized Fitness Coaching System",
    version="1.0.0",
)

# 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 生产环境换成具体域名
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时初始化数据库
@app.on_event("startup")
def startup():
    init_db()

# 注册路由
app.include_router(auth_router)
app.include_router(daily_router)
app.include_router(profile_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "FitGenie API"}