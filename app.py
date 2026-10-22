"""매크로 지표 카드와 국면 추이를 보여주는 Streamlit 대시보드."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from src.allocator import allocation_rows
from src.db_client import DBClient

I18N = {
    "ko": {
        "page_title": "매크로 펄스",
        "lang": "언어",
        "refresh": "데이터 갱신 / 분석",
        "refreshing": "FRED·가격 수집과 국면 판정을 실행하는 중입니다.",
        "refreshed": "갱신했습니다.",
        "current_regime": "현재 경기 국면",
        "as_of": "기준일",
        "regime_trend": "국면 추이",
        "portfolio": "추천 포트폴리오",
        "history": "지표 이력",
        "indicator": "지표",
        "range": "기간",
        "no_data": "저장된 데이터가 없습니다. 사이드바에서 갱신을 실행하거나 `python batch_pipeline.py`를 먼저 실행하세요.",
        "no_portfolio": "저장된 국면이 없어 추천 비중을 계산할 수 없습니다.",
        "no_history": "선택한 기간에 표시할 값이 없습니다.",
        "no_regime": "저장된 국면 이력이 없습니다.",
        "db_error": "Supabase 연결에 실패했습니다.",
        "schema_hint": "테이블이 없다면 table_create.sql을 Supabase SQL Editor에서 실행하세요.",
    },
    "en": {
        "page_title": "Macro Pulse",
        "lang": "Language",
        "refresh": "Refresh data / analysis",
        "refreshing": "Fetching FRED, prices, and classifying regimes.",
        "refreshed": "Refresh complete.",
        "current_regime": "Current Regime",
        "as_of": "As of",
        "regime_trend": "Regime History",
        "portfolio": "Recommended Portfolio",
        "history": "Indicator History",
        "indicator": "Indicator",
        "range": "Range",
        "no_data": "No stored data yet. Use the sidebar refresh or run `python batch_pipeline.py`.",
        "no_portfolio": "No regime is stored, so a recommended mix cannot be calculated.",
        "no_history": "No values to plot for the selected range.",
        "no_regime": "No regime history is stored yet.",
        "db_error": "Failed to connect to Supabase.",
        "schema_hint": "If the tables are missing, run table_create.sql in the Supabase SQL editor.",
    },
}

REGIME_COLORS = {
    config.REGIME_GOLDILOCKS: "#2ca02c",
    config.REGIME_OVERHEATING: "#ff7f0e",
    config.REGIME_STAGFLATION: "#d62728",
    config.REGIME_RECESSION: "#1f77b4",
}

SLEEVE_COLORS = {
    "us_equity": "#1f77b4",
    "us_bond": "#2ca02c",
    "australia": "#ff7f0e",
    "korea_equity": "#9467bd",
    "commodity": "#d62728",
}

HISTORY_WINDOWS = (
    ("5y", {"ko": "5년", "en": "5Y"}),
    ("1y", {"ko": "1년", "en": "1Y"}),
    ("6m", {"ko": "6개월", "en": "6M"}),
)


def _empty(error: str | None = None) -> dict:
    return {"market": pd.DataFrame(), "regimes": pd.DataFrame(), "error": error}


def _public_error(exc: BaseException) -> str:
    message = getattr(exc, "message", None)
    code = getattr(exc, "code", None)
    if message and code:
        return f"{code}: {message}"
    return str(exc)


@st.cache_data(ttl=300, show_spinner=False)
def _load_cached() -> dict:
    db = DBClient()
    market = db.fetch_frame(config.TABLE_MARKET, order_by="date", descending=False)
    regimes = db.fetch_frame(config.TABLE_REGIME, order_by="date", descending=False)
    return {"market": market, "regimes": regimes, "error": None}


def load_dashboard_data() -> dict:
    try:
        return _load_cached()
    except Exception as exc:
        return _empty(_public_error(exc))


def _fmt(value: float | None, digits: int = 2, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):,.{digits}f}{suffix}"


def _latest_number(row: pd.Series, column: str) -> float | None:
    if row.empty or column not in row or pd.isna(row[column]):
        return None
    return float(row[column])


def _regime_label(regime_en: str, lang: str) -> str:
    if lang == "ko":
        return config.REGIME_KR.get(regime_en, regime_en)
    return regime_en


def main() -> None:
    st.set_page_config(page_title="Macro Pulse", layout="wide")
    if "lang" not in st.session_state:
        st.session_state.lang = "ko"

    with st.sidebar:
        choice = st.radio(
            "언어 / Language",
            ["한국어", "English"],
            index=0 if st.session_state.lang == "ko" else 1,
        )
        st.session_state.lang = "ko" if choice == "한국어" else "en"
        lang = st.session_state.lang
        text = I18N[lang]
        st.caption(text["lang"])
        if st.button(text["refresh"], type="primary"):
            _run_refresh(text)

    lang = st.session_state.lang
    text = I18N[lang]
    st.title(text["page_title"])

    payload = load_dashboard_data()
    market: pd.DataFrame = payload["market"]
    regimes: pd.DataFrame = payload["regimes"]

    if payload.get("error"):
        st.error(f"{text['db_error']} {payload['error']}")
        if "PGRST205" in str(payload["error"]) or "Could not find the table" in str(payload["error"]):
            st.info(text["schema_hint"])
    elif market.empty:
        st.info(text["no_data"])

    latest = market.sort_values("date").iloc[-1] if not market.empty else pd.Series(dtype=float)
    _render_macro_metrics(lang, latest)
    _render_regime(text, lang, regimes)
    _render_portfolio(text, lang, regimes)
    _render_history(text, lang, market)


def _run_refresh(text: dict) -> None:
    from batch_pipeline import run

    with st.spinner(text["refreshing"]):
        try:
            summary = run()
        except Exception as exc:
            st.error(str(exc))
            return
    _load_cached.clear()
    regime_bit = summary.get("regime_en") or ""
    detail = f"{summary['as_of']} · {regime_bit}" if regime_bit else str(summary["as_of"])
    st.success(f"{text['refreshed']} {detail}")
    st.rerun()


def _metric_specs() -> list[dict]:
    return [spec for group in config.METRIC_GROUPS for spec in group["metrics"]]


def _render_macro_metrics(lang: str, latest: pd.Series) -> None:
    for group in config.METRIC_GROUPS:
        st.markdown(f"**{group[lang]}**")
        columns = st.columns(len(group["metrics"]))
        for column, spec in zip(columns, group["metrics"]):
            value = _latest_number(latest, spec["column"])
            column.metric(spec[lang], _fmt(value, digits=spec["digits"], suffix=spec["suffix"]))


def _render_regime(text: dict, lang: str, regimes: pd.DataFrame) -> None:
    st.subheader(text["current_regime"])
    if regimes.empty:
        st.info(text["no_regime"])
        return

    latest = regimes.sort_values("date").iloc[-1]
    regime_en = str(latest["regime_en"])
    regime_label = _regime_label(regime_en, lang)
    as_of = pd.to_datetime(latest["date"]).date()

    left, right = st.columns((0.7, 1.3))
    with left:
        _regime_banner(regime_en, regime_label)
        st.caption(f"{text['as_of']}: {as_of.isoformat()}")
    with right:
        st.plotly_chart(_regime_trend_figure(regimes, lang, text), width="stretch")


def _render_portfolio(text: dict, lang: str, regimes: pd.DataFrame) -> None:
    st.subheader(text["portfolio"])
    if regimes.empty:
        st.info(text["no_portfolio"])
        return

    latest = regimes.sort_values("date").iloc[-1]
    regime_en = str(latest["regime_en"])
    rows = allocation_rows(regime_en, lang)
    _, chart, _ = st.columns((1, 2, 1))
    with chart:
        st.plotly_chart(
            _portfolio_figure(rows, _regime_label(regime_en, lang)),
            width="stretch",
        )


def _portfolio_figure(rows: list[dict], center: str) -> go.Figure:
    fig = go.Figure(
        go.Pie(
            labels=[row["label"] for row in rows],
            values=[row["weight"] for row in rows],
            hole=0.58,
            sort=False,
            marker=dict(colors=[SLEEVE_COLORS[str(row["sleeve"])] for row in rows]),
            texttemplate="%{label}<br>%{value:.0f}%",
            hovertemplate="%{label}<br>%{value:.0f}%<extra></extra>",
        )
    )
    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        annotations=[
            dict(
                text=center,
                x=0.5,
                y=0.5,
                font=dict(size=16),
                showarrow=False,
            )
        ],
    )
    return fig


def _render_history(text: dict, lang: str, market: pd.DataFrame) -> None:
    st.subheader(text["history"])
    specs = _metric_specs()
    windows = {key: labels for key, labels in HISTORY_WINDOWS}
    pick, period = st.columns((2, 2))
    with pick:
        column = st.selectbox(
            text["indicator"],
            [spec["column"] for spec in specs],
            format_func=lambda key: next(spec[lang] for spec in specs if spec["column"] == key),
        )
    with period:
        window = st.radio(
            text["range"],
            list(windows),
            format_func=lambda key: windows[key][lang],
            horizontal=True,
        )

    spec = next(item for item in specs if item["column"] == column)
    if market.empty or column not in market.columns:
        st.info(text["no_history"])
        return

    history = market.copy()
    history["date"] = pd.to_datetime(history["date"])
    history = history.dropna(subset=[column])
    if history.empty:
        st.info(text["no_history"])
        return

    start = _window_start(history["date"].max(), str(window))
    history = history.loc[history["date"] >= start]
    if history.empty:
        st.info(text["no_history"])
        return

    st.plotly_chart(
        _history_figure(history, column, spec[lang], spec["suffix"]),
        width="stretch",
    )


def _window_start(end: pd.Timestamp, key: str) -> pd.Timestamp:
    if key == "5y":
        return end - pd.DateOffset(years=5)
    if key == "1y":
        return end - pd.DateOffset(years=1)
    return end - pd.DateOffset(months=6)


def _history_figure(history: pd.DataFrame, column: str, label: str, suffix: str) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=history["date"],
            y=history[column],
            mode="lines",
            line=dict(color="#1f4e79", width=2),
            hovertemplate=f"%{{x|%Y-%m-%d}}<br>%{{y}}{suffix}<extra></extra>",
            showlegend=False,
        )
    )
    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title=label,
    )
    return fig


def _regime_banner(regime_en: str, label: str) -> None:
    if regime_en == config.REGIME_GOLDILOCKS:
        st.success(label)
    elif regime_en == config.REGIME_OVERHEATING:
        st.warning(label)
    elif regime_en == config.REGIME_STAGFLATION:
        st.error(label)
    else:
        st.info(label)


def _regime_trend_figure(regimes: pd.DataFrame, lang: str, text: dict) -> go.Figure:
    history = regimes.copy()
    history["date"] = pd.to_datetime(history["date"])
    history["label"] = history["regime_en"].map(lambda key: _regime_label(str(key), lang))
    code = {name: index for index, name in enumerate(config.REGIMES)}
    history["code"] = history["regime_en"].map(code)
    fig = go.Figure(
        go.Scatter(
            x=history["date"],
            y=history["code"],
            mode="lines+markers",
            marker=dict(
                size=7,
                color=history["regime_en"].map(REGIME_COLORS),
            ),
            line=dict(color="#9aa0a6", width=1),
            customdata=history["label"],
            hovertemplate="%{x|%Y-%m-%d}<br>%{customdata}<extra></extra>",
            showlegend=False,
        )
    )
    fig.update_yaxes(
        tickmode="array",
        tickvals=list(code.values()),
        ticktext=[_regime_label(name, lang) for name in config.REGIMES],
        title=text["regime_trend"],
    )
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
    return fig


if __name__ == "__main__":
    main()
