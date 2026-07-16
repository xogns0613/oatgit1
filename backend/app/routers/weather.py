"""
실시간 위치 기반 날씨 API 연동 라우터
- [FR-2.2] 오픈 API(Open-Meteo)를 통한 기상 연동
- 기온에 따른 클로즈 레이어링 지수(clo) 계산
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
import requests

router = APIRouter(tags=["weather"])


class WeatherInfo(BaseModel):
    """날씨 정보 모델"""
    temperature: float        # 현재 기온 (°C)
    feels_like: float         # 체감 온도 (°C)
    condition: str            # 날씨 상태 (맑음, 흐림, 비 등)
    precipitation_prob: int   # 강수 확률 (%)
    humidity: int             # 습도 (%)
    clo_index: float          # 클로즈 레이어링 지수


def calculate_clo(temperature: float) -> float:
    """
    기온에 따른 클로즈 레이어링 지수(clo) 계산
    clo 값이 높을수록 두꺼운 옷이 필요함
    """
    if temperature >= 28:
        return 0.3   # 반팔, 반바지
    elif temperature >= 23:
        return 0.5   # 반팔, 얇은 긴바지
    elif temperature >= 20:
        return 0.7   # 얇은 긴팔, 긴바지
    elif temperature >= 17:
        return 1.0   # 가디건, 맨투맨
    elif temperature >= 12:
        return 1.5   # 자켓, 니트
    elif temperature >= 9:
        return 2.0   # 코트, 가죽자켓
    elif temperature >= 5:
        return 2.5   # 두꺼운 코트, 히트텍
    else:
        return 3.0   # 패딩, 목도리, 장갑


def wmo_code_to_condition(code: int) -> str:
    """WMO weather codes to string"""
    if code == 0: return "맑음"
    elif code in [1, 2, 3]: return "구름많음" if code == 3 else "흐림"
    elif code in [45, 48]: return "안개"
    elif code in [51, 53, 55, 56, 57]: return "이슬비"
    elif code in [61, 63, 65, 66, 67]: return "비"
    elif code in [71, 73, 75, 77]: return "눈"
    elif code in [80, 81, 82]: return "소나기"
    elif code in [85, 86]: return "눈"
    elif code in [95, 96, 99]: return "뇌우"
    return "맑음"


@router.get("/current", response_model=WeatherInfo)
async def get_current_weather(
    lat: float = Query(default=37.5665, description="위도 (기본: 서울)"),
    lon: float = Query(default=126.9780, description="경도 (기본: 서울)"),
):
    """
    현재 위치의 실시간 날씨 정보를 Open-Meteo API에서 가져옵니다.
    """
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,weather_code&timezone=auto"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        
        current = data.get("current", {})
        temp = current.get("temperature_2m", 22.0)
        feels = current.get("apparent_temperature", temp)
        humidity = current.get("relative_humidity_2m", 50)
        prob = current.get("precipitation_probability", 0) # Fallback to 0 if not present in current
        wmo_code = current.get("weather_code", 0)
        
        weather = WeatherInfo(
            temperature=temp,
            feels_like=feels,
            condition=wmo_code_to_condition(wmo_code),
            precipitation_prob=prob,
            humidity=humidity,
            clo_index=calculate_clo(temp),
        )
        return weather
    except Exception as e:
        print(f"Weather API Error: {e}, falling back to default.")
        temp = 22.0
        return WeatherInfo(
            temperature=temp,
            feels_like=20.5,
            condition="맑음",
            precipitation_prob=10,
            humidity=55,
            clo_index=calculate_clo(temp),
        )


@router.get("/recommendation-context")
async def get_weather_recommendation_context(
    lat: float = Query(default=37.5665, description="위도"),
    lon: float = Query(default=126.9780, description="경도"),
):
    """
    날씨 기반 코디 추천에 필요한 컨텍스트 정보를 반환합니다.
    - 온도 범위별 적합한 의류 레이어링 가이드
    """
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m&timezone=auto"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        temp = res.json().get("current", {}).get("temperature_2m", 22.0)
    except:
        temp = 22.0

    clo = calculate_clo(temp)

    if clo <= 0.5:
        layer_guide = "반팔 또는 민소매 상의에 얇은 하의가 적합합니다."
        recommended_categories = ["반팔티", "반바지", "린넨 셔츠"]
    elif clo <= 1.0:
        layer_guide = "얇은 긴팔 상의 또는 가벼운 가디건을 추천합니다."
        recommended_categories = ["긴팔티", "얇은 니트", "면바지"]
    elif clo <= 1.5:
        layer_guide = "자켓이나 가디건 레이어링이 좋습니다."
        recommended_categories = ["자켓", "니트", "슬랙스"]
    elif clo <= 2.0:
        layer_guide = "두꺼운 아우터와 따뜻한 이너를 매칭하세요."
        recommended_categories = ["코트", "맨투맨", "기모바지"]
    else:
        layer_guide = "패딩이나 롱코트가 필수입니다. 보온 액세서리도 챙기세요."
        recommended_categories = ["패딩", "히트텍", "목도리"]

    return {
        "temperature": temp,
        "clo_index": clo,
        "layer_guide": layer_guide,
        "recommended_categories": recommended_categories,
    }
