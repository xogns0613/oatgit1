from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .routers import images, weather, styling

app = FastAPI(title="Senior Fashion Coordinator Backend")

# CORS 미들웨어 설정 (프론트엔드와 백엔드가 다른 포트나 도메인에서 돌 때 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(images.router, prefix="/api/images")
app.include_router(weather.router, prefix="/api/weather")
app.include_router(styling.router, prefix="/api/styling")

# 업로드 폴더 절대 경로 설정 및 서빙
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 프론트엔드 정적 파일 서빙
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

