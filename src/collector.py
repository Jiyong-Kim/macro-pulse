"""FRED 거시 지표와 yfinance 가격을 날짜 기준으로 맞춘다."""

from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf
from fredapi import Fred

import config

logger = logging.getLogger(__name__)

_PRICE_FFILL_LIMIT = 5


def _normalize_index(index: pd.Index) -> pd.DatetimeIndex:
    dates = pd.to_datetime(index, utc=True, errors="coerce")
    return pd.DatetimeIndex(dates).tz_convert(None).normalize()


def _fred_key(api_key: str | None) -> str:
    if api_key is not None:
        return api_key.strip()
    return config.FRED_API_KEY


def _empty_fred() -> pd.DataFrame:
    return pd.DataFrame(columns=list(config.FRED_SERIES))


def _year_over_year(series: pd.Series) -> pd.Series:
    """월간 지수 12칸 전 대비 변화율(%). CPI처럼 월 1회 발표되는 시리즈용이다."""
    values = pd.to_numeric(series, errors="coerce")
    yoy = (values / values.shift(12) - 1.0) * 100.0
    yoy.name = series.name
    return yoy


def fetch_fred(start: str | None = None, api_key: str | None = None) -> pd.DataFrame:
    """FRED 시계열을 FRED_SERIES 컬럼의 와이드 프레임으로 반환한다.

    cpi_yoy는 원지수 대신 전년 대비 변화율이다.
    API 키가 없으면 예외 없이 빈 프레임을 반환한다.
    """
    key = _fred_key(api_key)
    if not key:
        logger.warning("FRED_API_KEY가 없어 거시 지표 수집을 건너뜁니다.")
        return _empty_fred()

    fred = Fred(api_key=key)
    start = start or config.START_DATE
    frames: list[pd.Series] = []

    for column, series_id in config.FRED_SERIES.items():
        try:
            series = fred.get_series(series_id, observation_start=start)
        except Exception as exc:
            logger.warning("FRED 수집 실패: %s (%s): %s", column, series_id, exc)
            continue
        if series is None or series.empty:
            logger.warning("FRED 빈 시리즈: %s (%s)", column, series_id)
            continue
        series = series.copy()
        series.index = _normalize_index(series.index)
        series = series[~series.index.isna()].sort_index()
        series.name = column
        if column in config.FRED_YOY_COLUMNS:
            series = _year_over_year(series)
        frames.append(series)
        logger.info("FRED 수집: %s %s행", series_id, len(series))

    if not frames:
        logger.warning("FRED에서 가져온 지표가 없습니다. Yahoo Finance 가격만 사용합니다.")
        return _empty_fred()

    wide = pd.concat(frames, axis=1).sort_index()
    wide = wide.groupby(level=0).last()
    missing = [series_id for column, series_id in config.FRED_SERIES.items() if column not in wide.columns]
    if missing:
        raise RuntimeError(f"FRED 시리즈를 가져오지 못했습니다: {', '.join(missing)}")
    return wide[list(config.FRED_SERIES)]


def fetch_prices(start: str | None = None) -> pd.DataFrame:
    """조정 종가를 spy, qqq, tlt, ioz_ax, vgb_ax, kospi, dbc 컬럼으로 반환한다."""
    start = start or config.START_DATE
    ticker_to_column = {ticker: column for column, ticker in config.TICKERS.items()}
    tickers = list(ticker_to_column)
    raw = yf.download(
        tickers=tickers,
        start=start,
        auto_adjust=True,
        progress=False,
        threads=False,
        group_by="column",
    )
    if raw is None or raw.empty:
        raise RuntimeError("yfinance 가격 데이터가 비어 있습니다.")

    close = _extract_close(raw, tickers)
    close.index = _normalize_index(close.index)
    close = close.loc[close.index.notna()].sort_index()
    close = close.groupby(level=0).last()
    close = close.rename(columns=ticker_to_column)
    for column in config.TICKERS:
        if column not in close.columns:
            close[column] = pd.NA
    close = close[list(config.TICKERS)]
    logger.info("yfinance 수집: %s행", len(close))
    return close


def build_market_frame(fred: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """거래일 달력에 거시 지표를 앞당김(ffill)으로 붙이고 결측을 정리한다.

    월간 FRED 지표는 다음 발표 전까지 마지막 값을 유지한다.
    거래소 휴장으로 생긴 가격 공백은 최대 5거래일만 채운다.
    """
    macro = fred.sort_index()
    if not macro.empty:
        macro = macro.ffill()
    px = prices.sort_index()
    panel = px.join(macro, how="left").sort_index()

    macro_cols = [col for col in config.FRED_SERIES if col in panel.columns]
    price_cols = [col for col in config.TICKERS if col in panel.columns]
    if macro_cols and not macro.empty:
        panel[macro_cols] = panel[macro_cols].ffill()
    panel[price_cols] = panel[price_cols].ffill(limit=_PRICE_FFILL_LIMIT)

    # 거시 지표가 있을 때만 해당 결측 행을 버린다. 키가 없으면 가격 행을 유지한다.
    required_macro = [col for col in ("fed_funds", "t10y2y", "unrate") if col in panel.columns and panel[col].notna().any()]
    if required_macro:
        panel = panel.dropna(subset=required_macro, how="any")
    panel = panel.dropna(subset=price_cols, how="all")

    frame = panel.reset_index()
    date_col = "index" if "index" in frame.columns else frame.columns[0]
    frame = frame.rename(columns={date_col: "date"})
    frame["date"] = pd.to_datetime(frame["date"]).dt.date
    for column in config.MARKET_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
        frame[column] = pd.to_numeric(frame[column], errors="coerce").round(2)
    frame = frame.drop_duplicates(subset=["date"], keep="last")
    return frame[["date", *config.MARKET_COLUMNS]].sort_values("date").reset_index(drop=True)


def collect_market_data(start: str | None = None) -> pd.DataFrame:
    if not config.FRED_API_KEY:
        logger.warning("FRED_API_KEY가 없어 Yahoo Finance 가격만 수집합니다.")
        return build_market_frame(_empty_fred(), fetch_prices(start=start))
    return build_market_frame(fetch_fred(start=start), fetch_prices(start=start))


def _extract_close(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    if isinstance(raw.columns, pd.MultiIndex):
        level0 = set(raw.columns.get_level_values(0))
        if "Close" in level0:
            close = raw["Close"].copy()
        elif "Adj Close" in level0:
            close = raw["Adj Close"].copy()
        else:
            close = raw.xs(raw.columns.levels[-1][0], axis=1, level=-1)
        if isinstance(close, pd.Series):
            close = close.to_frame(name=tickers[0])
        close.columns = [str(col) for col in close.columns]
        return close

    if "Close" in raw.columns and len(tickers) == 1:
        return raw[["Close"]].rename(columns={"Close": tickers[0]})
    return raw.copy()
