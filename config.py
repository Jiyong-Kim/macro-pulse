"""환경변수, FRED 지표 ID, 자산 티커, 국면 라벨."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

FRED_API_KEY = os.getenv("FRED_API_KEY", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

START_DATE = "2020-01-01"
TREND_MONTHS = 3
UNEMP_DEADBAND = 0.10  # 3개월 실업률 변화(퍼센트포인트) 무반응 구간
RATE_DEADBAND = 0.10  # 3개월 기준금리 변화(퍼센트포인트) 무반응 구간

# 컬럼명 → FRED series id. 테이블 mp_macro_market_data 컬럼과 1:1.
# cpi_yoy는 CPIAUCSL 원지수를 받아 12개월 전 대비 변화율로 저장한다.
FRED_SERIES: dict[str, str] = {
    "fed_funds": "FEDFUNDS",
    "dgs3m": "DGS3MO",
    "dgs2": "DGS2",
    "dgs10": "DGS10",
    "dgs30": "DGS30",
    "t10y2y": "T10Y2Y",
    "t10y3m": "T10Y3M",
    "hy_spread": "BAMLH0A0HYM2",
    "unrate": "UNRATE",
    "cpi_yoy": "CPIAUCSL",
    "m2sl": "M2SL",
    "dollar": "DTWEXBGS",
}

FRED_YOY_COLUMNS = frozenset({"cpi_yoy"})

# 컬럼명 → yfinance 티커.
TICKERS: dict[str, str] = {
    "spy": "SPY",
    "qqq": "QQQ",
    "tlt": "TLT",
    "ioz_ax": "IOZ.AX",
    "vgb_ax": "VGB.AX",
    "kospi": "^KS11",
    "dbc": "DBC",
}

MARKET_COLUMNS = list(FRED_SERIES) + list(TICKERS)

TABLE_MARKET = "mp_macro_market_data"
TABLE_REGIME = "mp_regime_history"

REGIME_GOLDILOCKS = "Goldilocks"
REGIME_OVERHEATING = "Overheating"
REGIME_STAGFLATION = "Stagflation"
REGIME_RECESSION = "Recession"
REGIMES = (
    REGIME_GOLDILOCKS,
    REGIME_OVERHEATING,
    REGIME_STAGFLATION,
    REGIME_RECESSION,
)

REGIME_KR: dict[str, str] = {
    REGIME_GOLDILOCKS: "골디락스",
    REGIME_OVERHEATING: "과열",
    REGIME_STAGFLATION: "스태그플레이션",
    REGIME_RECESSION: "침체",
}

# 배분 파이 차트에 쓰는 5개 슬리브.
SLEEVES: dict[str, dict[str, str]] = {
    "us_equity": {"en": "US Equities", "ko": "미국 주식"},
    "us_bond": {"en": "US Bonds", "ko": "미국 채권"},
    "australia": {"en": "Australian Assets", "ko": "호주 자산"},
    "korea_equity": {"en": "Korean Equities", "ko": "한국 주식"},
    "commodity": {"en": "Commodities", "ko": "원자재"},
}

# 대시보드 카드. column은 시장 테이블 컬럼, suffix는 표시 단위.
METRIC_GROUPS: list[dict] = [
    {
        "ko": "금리",
        "en": "Rates",
        "metrics": [
            {"column": "fed_funds", "ko": "기준금리", "en": "Fed Funds", "digits": 2, "suffix": "%"},
            {"column": "dgs3m", "ko": "3개월", "en": "3M Yield", "digits": 2, "suffix": "%"},
            {"column": "dgs2", "ko": "2년", "en": "2Y Yield", "digits": 2, "suffix": "%"},
            {"column": "dgs10", "ko": "10년", "en": "10Y Yield", "digits": 2, "suffix": "%"},
            {"column": "dgs30", "ko": "30년", "en": "30Y Yield", "digits": 2, "suffix": "%"},
        ],
    },
    {
        "ko": "금리차",
        "en": "Spreads",
        "metrics": [
            {"column": "t10y2y", "ko": "10년-2년", "en": "10Y–2Y", "digits": 2, "suffix": "%"},
            {"column": "t10y3m", "ko": "10년-3개월", "en": "10Y–3M", "digits": 2, "suffix": "%"},
            {"column": "hy_spread", "ko": "하이일드", "en": "HY Spread", "digits": 2, "suffix": "%"},
        ],
    },
    {
        "ko": "경기·물가",
        "en": "Activity",
        "metrics": [
            {"column": "unrate", "ko": "실업률", "en": "Unemployment", "digits": 2, "suffix": "%"},
            {"column": "cpi_yoy", "ko": "CPI 전년비", "en": "CPI YoY", "digits": 2, "suffix": "%"},
            {"column": "m2sl", "ko": "M2 통화량", "en": "M2 Money Stock", "digits": 0, "suffix": ""},
            {"column": "dollar", "ko": "달러지수", "en": "Dollar Index", "digits": 2, "suffix": ""},
        ],
    },
    {
        "ko": "시장",
        "en": "Markets",
        "metrics": [
            {"column": "spy", "ko": "SPY", "en": "SPY", "digits": 2, "suffix": ""},
            {"column": "kospi", "ko": "KOSPI", "en": "KOSPI", "digits": 2, "suffix": ""},
            {"column": "ioz_ax", "ko": "ASX", "en": "ASX", "digits": 2, "suffix": ""},
        ],
    },
]

PRICE_CHART_COLUMNS = ("spy", "tlt", "ioz_ax", "kospi", "dbc")
PRICE_LABELS: dict[str, dict[str, str]] = {
    "spy": {"en": "S&P 500 (SPY)", "ko": "미국 S&P 500 (SPY)"},
    "qqq": {"en": "Nasdaq 100 (QQQ)", "ko": "미국 나스닥 100 (QQQ)"},
    "tlt": {"en": "US Long Treasury (TLT)", "ko": "미국 장기채 (TLT)"},
    "ioz_ax": {"en": "ASX 200 (IOZ.AX)", "ko": "호주 ASX 200 (IOZ.AX)"},
    "vgb_ax": {"en": "AU Gov Bond (VGB.AX)", "ko": "호주 국채 (VGB.AX)"},
    "kospi": {"en": "KOSPI", "ko": "한국 KOSPI"},
    "dbc": {"en": "Commodities (DBC)", "ko": "원자재 (DBC)"},
}


def require_env(name: str, value: str) -> str:
    if not value:
        raise RuntimeError(f"환경변수 {name}가 설정되지 않았습니다. .env 파일을 확인하세요.")
    return value
