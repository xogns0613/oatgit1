"""
하이브리드 코디 매칭 및 스타일 추천 엔진 라우터
- [FR-3.1] 오늘 날씨 & TPO 맞춤형 코디 제안
- [FR-3.2] 부족한 아이템 스마트 쇼핑 추천
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
import random
import requests

from .images import closet_db
from .weather import calculate_clo

router = APIRouter(tags=["styling"])

class BodyProfile(BaseModel):
    gender: str = "남성"
    height_cm: float = 175.0
    weight_kg: float = 70.0
    body_type: Optional[str] = "표준형"

class CodiItem(BaseModel):
    category: str
    name: str
    color: str
    image_url: Optional[str] = None

class CodiRecommendation(BaseModel):
    codi_id: int
    items: list[CodiItem]
    reasoning: str
    missing_items: list[dict] = []

class StylingRequest(BaseModel):
    tpo: str = "출근"
    body_profile: Optional[BodyProfile] = None

user_profiles: dict[str, BodyProfile] = {}

def get_current_temperature(lat=37.5665, lon=126.9780) -> float:
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m&timezone=auto"
        res = requests.get(url, timeout=3)
        res.raise_for_status()
        return res.json().get("current", {}).get("temperature_2m", 22.0)
    except:
        return 22.0

def generate_reasoning(tpo: str, temp: float, has_outer: bool, is_missing: bool) -> str:
    """날씨와 TPO에 따른 코디 사유 생성"""
    reason = f"현재 기온 {temp}도에 맞춘 {tpo}용 코디입니다. "
    if has_outer:
        reason += "일교차를 대비해 가벼운 아우터를 매치했습니다. "
    else:
        reason += "아우터 없이 가볍게 입기 좋은 구성입니다. "
    
    if is_missing:
        reason += "옷장에 부족한 아이템은 쇼핑 추천을 참고해 보세요!"
    else:
        reason += "옷장에 있는 아이템만으로 완벽한 코디가 완성되었습니다."
    return reason

@router.post("/recommend", response_model=list[CodiRecommendation])
async def recommend_codi(request: StylingRequest):
    tpo = request.tpo
    temp = get_current_temperature()
    clo = calculate_clo(temp)
    
    # 옷장에 있는 옷 분류
    tops = [item for item in closet_db.values() if item.tags.category == "상의"]
    bottoms = [item for item in closet_db.values() if item.tags.category == "하의"]
    outers = [item for item in closet_db.values() if item.tags.category == "아우터"]
    
    needs_outer = clo >= 1.0
    
    recommendations = []
    
    # 3개의 추천 코디 생성
    for i in range(1, 4):
        items = []
        missing = []
        is_missing = False
        
        # 1. 상의 선택
        if tops:
            top = random.choice(tops)
            items.append(CodiItem(category="상의", name=top.tags.sub_category, color=top.tags.color, image_url=top.nukki_image_url))
        else:
            items.append(CodiItem(category="상의", name="기본 무지 티셔츠", color="화이트"))
            missing.append({"name": "기본 무지 티셔츠", "reason": "모든 코디의 기본이 되는 이너", "shop_url": "https://www.musinsa.com"})
            is_missing = True
            
        # 2. 하의 선택
        if bottoms:
            bottom = random.choice(bottoms)
            items.append(CodiItem(category="하의", name=bottom.tags.sub_category, color=bottom.tags.color, image_url=bottom.nukki_image_url))
        else:
            bottom_name = "슬랙스" if tpo == "출근" else "데님 팬츠"
            items.append(CodiItem(category="하의", name=f"베이직 {bottom_name}", color="블랙"))
            missing.append({"name": f"베이직 {bottom_name}", "reason": f"{tpo}에 가장 활용도가 높은 팬츠", "shop_url": "https://www.musinsa.com"})
            is_missing = True
            
        # 3. 아우터 선택 (날씨가 쌀쌀할 때)
        has_outer = False
        if needs_outer:
            has_outer = True
            if outers:
                outer = random.choice(outers)
                items.append(CodiItem(category="아우터", name=outer.tags.sub_category, color=outer.tags.color, image_url=outer.nukki_image_url))
            else:
                outer_name = "블레이저" if tpo == "출근" else "가디건"
                items.append(CodiItem(category="아우터", name=f"깔끔한 {outer_name}", color="네이비"))
                missing.append({"name": f"깔끔한 {outer_name}", "reason": f"지금 날씨에 꼭 필요한 {tpo} 아우터", "shop_url": "https://www.musinsa.com"})
                is_missing = True
                
        reasoning = generate_reasoning(tpo, temp, has_outer, is_missing)
        
        recommendations.append(CodiRecommendation(
            codi_id=i,
            items=items,
            reasoning=reasoning,
            missing_items=missing
        ))
        
    return recommendations


@router.post("/profile", response_model=BodyProfile)
async def save_body_profile(profile: BodyProfile, user_id: str = Query(default="default")):
    user_profiles[user_id] = profile
    return profile


@router.get("/profile", response_model=BodyProfile)
async def get_body_profile(user_id: str = Query(default="default")):
    if user_id not in user_profiles:
        return BodyProfile()
    return user_profiles[user_id]
