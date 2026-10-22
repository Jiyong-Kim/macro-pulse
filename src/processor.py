"""수익률 곡선, 실업, 기준금리 방향으로 4개 경기 국면을 판정한다."""

from __future__ import annotations

import logging

import pandas as pd

import config

logger = logging.getLogger(__name__)


def _regime(curve: float, unrate_chg: float, fed_chg: float) -> str:
    """세 신호의 우선순위로 국면을 고른다.

    - 침체: 장단기 금리차가 역전됐는데 실업이 늘거나, 실업이 느는데 금리를 내리거나,
      곡선이 역전된 채 금리도 내려가는 구간.
    - 스태그플레이션: 실업이 느는데도 기준금리를 올리는 구간.
    - 과열: 실업이 늘지 않는데 기준금리를 올리는 구간.
    - 골디락스: 곡선이 정상적이고 실업·금리가 안정적이거나 완화적인 나머지 구간.
    """
    inverted = curve < 0
    unemp_up = unrate_chg > config.UNEMP_DEADBAND
    rates_up = fed_chg > config.RATE_DEADBAND
    rates_down = fed_chg < -config.RATE_DEADBAND

    if unemp_up and inverted:
        return config.REGIME_RECESSION
    if unemp_up and rates_up:
        return config.REGIME_STAGFLATION
    if unemp_up and rates_down:
        return config.REGIME_RECESSION
    if rates_up:
        return config.REGIME_OVERHEATING
    if inverted and rates_down:
        return config.REGIME_RECESSION
    return config.REGIME_GOLDILOCKS


def classify_regimes(market: pd.DataFrame) -> pd.DataFrame:
    """월말 관측으로 국면을 판정하고 mp_regime_history 적재용 프레임을 반환한다."""
    empty = pd.DataFrame(columns=["date", "regime_en", "regime_kr"])
    if market.empty:
        return empty

    monthly = market.copy()
    monthly["date"] = pd.to_datetime(monthly["date"])
    monthly = monthly.set_index("date").sort_index().resample("ME").last()
    needed = {"t10y2y", "unrate", "fed_funds"}
    if not needed.issubset(monthly.columns):
        logger.warning("국면 판정에 필요한 컬럼이 없습니다: %s", sorted(needed - set(monthly.columns)))
        return empty

    features = pd.DataFrame(
        {
            "t10y2y": monthly["t10y2y"],
            "unrate_chg_3m": monthly["unrate"].diff(config.TREND_MONTHS),
            "fed_chg_3m": monthly["fed_funds"].diff(config.TREND_MONTHS),
        }
    ).dropna()
    if features.empty:
        logger.warning("국면 판정에 필요한 3개월 변화가 부족합니다.")
        return empty

    regime_en = [
        _regime(float(row.t10y2y), float(row.unrate_chg_3m), float(row.fed_chg_3m))
        for row in features.itertuples(index=False)
    ]
    result = pd.DataFrame(
        {
            "date": pd.to_datetime(features.index).date,
            "regime_en": regime_en,
        }
    )
    result["regime_kr"] = result["regime_en"].map(config.REGIME_KR)
    logger.info("국면 시계열: %s행, 최근=%s", len(result), result["regime_en"].iloc[-1])
    return result.reset_index(drop=True)
