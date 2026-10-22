"""현재 경기 국면에 따른 목표 배분 비중(%)."""

from __future__ import annotations

import config

# 다섯 슬리브 합은 100. 국면이 바뀔 때의 방향만 담은 전략 비중이며,
# 최적화 결과가 아니다.
REGIME_WEIGHTS: dict[str, dict[str, float]] = {
    config.REGIME_GOLDILOCKS: {
        "us_equity": 40,
        "us_bond": 20,
        "australia": 15,
        "korea_equity": 15,
        "commodity": 10,
    },
    config.REGIME_OVERHEATING: {
        "us_equity": 25,
        "us_bond": 10,
        "australia": 15,
        "korea_equity": 10,
        "commodity": 40,
    },
    config.REGIME_STAGFLATION: {
        "us_equity": 10,
        "us_bond": 15,
        "australia": 15,
        "korea_equity": 5,
        "commodity": 55,
    },
    config.REGIME_RECESSION: {
        "us_equity": 15,
        "us_bond": 50,
        "australia": 12,
        "korea_equity": 8,
        "commodity": 15,
    },
}


def allocate(regime_en: str) -> dict[str, float]:
    """국면 이름(영문)에 대한 슬리브별 비중(%)을 반환한다."""
    if regime_en not in REGIME_WEIGHTS:
        raise KeyError(f"지원하지 않는 국면입니다: {regime_en}")
    weights = dict(REGIME_WEIGHTS[regime_en])
    total = sum(weights.values())
    if abs(total - 100) > 1e-6:
        raise ValueError(f"{regime_en} 비중 합이 100이 아닙니다: {total}")
    return weights


def allocation_rows(regime_en: str, lang: str = "en") -> list[dict[str, float | str]]:
    label_key = "ko" if lang == "ko" else "en"
    weights = allocate(regime_en)
    return [
        {
            "sleeve": sleeve,
            "label": config.SLEEVES[sleeve][label_key],
            "weight": weight,
        }
        for sleeve, weight in weights.items()
    ]
