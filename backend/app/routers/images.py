"""
이미지 업로드 및 배경 제거(누끼), AI 자동 태깅 라우터
- [FR-1.1] 옷 사진 업로드 및 자동 배경 제거
- [FR-1.2] AI 자동 의류 태깅 (랜덤 생성으로 모사)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import random

router = APIRouter(tags=["images"])

# ── 임시 저장 디렉토리 ──
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


class ClothingTag(BaseModel):
    """의류 자동 태깅 결과 모델"""
    category: str = "상의"          # 상의/하의/아우터/원피스/신발/액세서리
    sub_category: str = "티셔츠"    # 셔츠, 니트, 슬랙스, 데님 등
    color: str = "블랙"             # 대표 색상명
    pattern: str = "무지"           # 무지, 스트라이프, 체크, 도트 등
    season: str = "사계절"          # 봄, 여름, 가을, 겨울, 사계절


class ClothingItem(BaseModel):
    """디지털 옷장에 등록된 의류 아이템"""
    id: str
    filename: str
    original_image_url: str
    nukki_image_url: Optional[str] = None
    tags: ClothingTag


# ── 임시 인메모리 저장소 (MVP) ──
closet_db: dict[str, ClothingItem] = {}


def generate_mock_tags() -> ClothingTag:
    """MVP 프로토타입용 무작위 태그 생성기"""
    categories = {
        "상의": ["티셔츠", "셔츠", "니트", "맨투맨"],
        "하의": ["슬랙스", "데님", "면바지", "반바지"],
        "아우터": ["자켓", "코트", "패딩", "블레이저"]
    }
    cat = random.choice(list(categories.keys()))
    sub_cat = random.choice(categories[cat])
    colors = ["블랙", "화이트", "그레이", "네이비", "베이지", "브라운", "라이트 블루", "카키"]
    patterns = ["무지", "무지", "무지", "스트라이프", "체크"]
    seasons = ["사계절", "사계절", "여름", "겨울", "봄/가을"]
    
    return ClothingTag(
        category=cat,
        sub_category=sub_cat,
        color=random.choice(colors),
        pattern=random.choice(patterns),
        season=random.choice(seasons)
    )


@router.post("/upload", response_model=ClothingItem)
async def upload_clothing_image(file: UploadFile = File(...)):
    """
    옷 사진을 업로드하면:
    1. 파일 저장
    2. 배경 제거(누끼) 처리 (MVP에서는 원본 그대로 사용)
    3. AI 자동 태깅 (MVP: 랜덤 그럴싸한 태그 부여)
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    item_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "image.jpg")[1]
    saved_filename = f"{item_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    tags = generate_mock_tags()

    item = ClothingItem(
        id=item_id,
        filename=saved_filename,
        original_image_url=f"/uploads/{saved_filename}",
        nukki_image_url=f"/uploads/{saved_filename}",  # MVP: 원본 그대로
        tags=tags,
    )
    closet_db[item_id] = item
    return item


@router.get("/closet", response_model=list[ClothingItem])
async def get_closet():
    """디지털 옷장에 등록된 모든 의류 목록 조회"""
    return list(closet_db.values())


@router.get("/closet/{item_id}", response_model=ClothingItem)
async def get_clothing_item(item_id: str):
    """특정 의류 아이템 상세 조회"""
    if item_id not in closet_db:
        raise HTTPException(status_code=404, detail="해당 의류를 찾을 수 없습니다.")
    return closet_db[item_id]


@router.put("/closet/{item_id}/tags", response_model=ClothingItem)
async def update_clothing_tags(item_id: str, tags: ClothingTag):
    """AI 태깅 결과 수동 수정 (사용자가 드롭다운으로 태그를 수정)"""
    if item_id not in closet_db:
        raise HTTPException(status_code=404, detail="해당 의류를 찾을 수 없습니다.")
    closet_db[item_id].tags = tags
    return closet_db[item_id]


@router.delete("/closet/{item_id}")
async def delete_clothing_item(item_id: str):
    """옷장에서 의류 삭제"""
    if item_id not in closet_db:
        raise HTTPException(status_code=404, detail="해당 의류를 찾을 수 없습니다.")
    del closet_db[item_id]
    return {"message": "삭제되었습니다.", "id": item_id}
