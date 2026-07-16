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

SHOPPING_MOCKS = {
    "무지 티셔츠": [
        {
            "brand": "무신사 스탠다드",
            "name": "릴렉스 핏 크루 넥 반팔 티셔츠",
            "price": "13,900원",
            "image_url": "https://image.msscdn.net/images/goods_img/20210324/1858596/1858596_1_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=무신사+스탠다드+반팔+티셔츠"
        },
        {
            "brand": "수피마",
            "name": "코튼 베이식 반팔 티셔츠",
            "price": "18,900원",
            "image_url": "https://image.msscdn.net/images/goods_img/20200424/1420713/1420713_4_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=수피마+반팔"
        }
    ],
    "셔츠": [
        {
            "brand": "무신사 스탠다드",
            "name": "베이식 옥스퍼드 셔츠",
            "price": "29,900원",
            "image_url": "https://image.msscdn.net/images/goods_img/20190823/1127076/1127076_1_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=무신사+스탠다드+옥스퍼드+셔츠"
        }
    ],
    "니트": [
        {
            "brand": "수아레",
            "name": "하프 집업 니트",
            "price": "49,900원",
            "image_url": "https://image.msscdn.net/images/goods_img/20210825/2088899/2088899_1_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=수아레+하프+집업+니트"
        }
    ],
    "슬랙스": [
        {
            "brand": "무신사 스탠다드",
            "name": "와이드 히든 밴딩 슬랙스",
            "price": "33,900원",
            "image_url": "https://image.msscdn.net/images/goods_img/20190228/970714/970714_3_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=무신사+스탠다드+와이드+슬랙스"
        },
        {
            "brand": "컨셉원",
            "name": "테이퍼드 히든밴딩 슬랙스",
            "price": "39,800원",
            "image_url": "https://image.msscdn.net/images/goods_img/20200813/1547849/1547849_1_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=컨셉원+슬랙스"
        }
    ],
    "데님 팬츠": [
        {
            "brand": "토피",
            "name": "와이드 데님 팬츠",
            "price": "49,000원",
            "image_url": "https://image.msscdn.net/images/goods_img/20180219/715454/715454_3_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=토피+와이드+데님"
        },
        {
            "brand": "피스워커",
            "name": "스톤 워시드 데님",
            "price": "52,000원",
            "image_url": "https://image.msscdn.net/images/goods_img/20190220/961111/961111_1_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=피스워커+데님"
        }
    ],
    "면바지": [
        {
            "brand": "지오다노",
            "name": "테이퍼드 치노 팬츠",
            "price": "29,800원",
            "image_url": "https://image.msscdn.net/images/goods_img/20200115/1271638/1271638_1_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=지오다노+치노+팬츠"
        }
    ],
    "가디건": [
        {
            "brand": "쿠어",
            "name": "오버핏 부클 가디건",
            "price": "79,000원",
            "image_url": "https://image.msscdn.net/images/goods_img/20200827/1566412/1566412_1_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=쿠어+가디건"
        }
    ],
    "블레이저": [
        {
            "brand": "무신사 스탠다드",
            "name": "베이식 블레이저",
            "price": "69,900원",
            "image_url": "https://image.msscdn.net/images/goods_img/20190228/970716/970716_1_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=무신사+스탠다드+블레이저"
        }
    ],
    "코트": [
        {
            "brand": "인사일런스",
            "name": "솔리스트 캐시미어 코트",
            "price": "189,000원",
            "image_url": "https://image.msscdn.net/images/goods_img/20170914/634731/634731_4_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=인사일런스+캐시미어+코트"
        }
    ],
    "패딩": [
        {
            "brand": "내셔널지오그래픽",
            "name": "타루가 RDS 숏패딩",
            "price": "299,000원",
            "image_url": "https://image.msscdn.net/images/goods_img/20200730/1529126/1529126_3_500.jpg",
            "link": "https://www.musinsa.com/search/musinsa/goods?q=내셔널지오그래픽+타루가"
        }
    ]
}

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
    
    basic_tops = [("무지 티셔츠", "화이트"), ("셔츠", "스카이블루"), ("니트", "네이비")]
    basic_bottoms = [("슬랙스", "블랙"), ("데님 팬츠", "블루"), ("면바지", "베이지")]
    basic_outers = [("블레이저", "네이비"), ("가디건", "그레이"), ("코트", "블랙") if clo >= 1.5 else ("패딩", "블랙")]
    
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
            top_name, top_color = basic_tops[(i-1) % len(basic_tops)]
            items.append(CodiItem(category="상의", name=f"기본 {top_name}", color=top_color))
            missing.append({"name": f"기본 {top_name}", "reason": "모든 코디의 기본이 되는 이너", "products": SHOPPING_MOCKS.get(top_name, [])})
            is_missing = True
            
        # 2. 하의 선택
        if bottoms:
            bottom = random.choice(bottoms)
            items.append(CodiItem(category="하의", name=bottom.tags.sub_category, color=bottom.tags.color, image_url=bottom.nukki_image_url))
        else:
            bot_name, bot_color = basic_bottoms[(i-1) % len(basic_bottoms)]
            items.append(CodiItem(category="하의", name=f"베이직 {bot_name}", color=bot_color))
            missing.append({"name": f"베이직 {bot_name}", "reason": f"활용도가 가장 높은 팬츠", "products": SHOPPING_MOCKS.get(bot_name, [])})
            is_missing = True
            
        # 3. 아우터 선택 (날씨가 쌀쌀할 때)
        has_outer = False
        if needs_outer:
            has_outer = True
            if outers:
                outer = random.choice(outers)
                items.append(CodiItem(category="아우터", name=outer.tags.sub_category, color=outer.tags.color, image_url=outer.nukki_image_url))
            else:
                out_name, out_color = basic_outers[(i-1) % len(basic_outers)]
                items.append(CodiItem(category="아우터", name=f"깔끔한 {out_name}", color=out_color))
                missing.append({"name": f"깔끔한 {out_name}", "reason": f"지금 날씨에 꼭 필요한 아우터", "products": SHOPPING_MOCKS.get(out_name, [])})
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
