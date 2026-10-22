"""수집 → 국면 판정 → Supabase 업서트를 한 번에 실행한다."""

from __future__ import annotations

import logging
from typing import Any

import config
from src.collector import collect_market_data
from src.db_client import DBClient, records_from_frame
from src.processor import classify_regimes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("batch_pipeline")


def run(start: str | None = None) -> dict[str, Any]:
    logger.info("시장·거시 데이터 수집 시작")
    market = collect_market_data(start=start)
    if market.empty:
        raise RuntimeError("정렬된 시장 데이터가 비어 있습니다.")

    regimes = classify_regimes(market)
    db = DBClient()
    market_rows = db.upsert(config.TABLE_MARKET, records_from_frame(market))

    if regimes.empty:
        logger.warning("거시 지표가 없어 국면 판정을 건너뛰고 가격만 저장합니다.")
        as_of = market.iloc[-1]["date"]
        summary = {
            "market_rows": market_rows,
            "regime_rows": 0,
            "as_of": as_of.isoformat(),
            "regime_en": None,
            "regime_kr": None,
        }
        logger.info("배치 완료: as_of=%s market=%s", summary["as_of"], summary["market_rows"])
        return summary

    regime_rows = db.upsert(config.TABLE_REGIME, records_from_frame(regimes))
    latest = regimes.iloc[-1]
    summary = {
        "market_rows": market_rows,
        "regime_rows": regime_rows,
        "as_of": latest["date"].isoformat(),
        "regime_en": str(latest["regime_en"]),
        "regime_kr": str(latest["regime_kr"]),
    }
    logger.info(
        "배치 완료: as_of=%s regime=%s market=%s regime_rows=%s",
        summary["as_of"],
        summary["regime_en"],
        summary["market_rows"],
        summary["regime_rows"],
    )
    return summary


if __name__ == "__main__":
    run()
