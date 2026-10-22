"""Supabase 연결, 업서트, 조회."""

from __future__ import annotations

import logging
import math
from datetime import date, datetime
from typing import Any

import pandas as pd
from supabase import Client, create_client

import config

logger = logging.getLogger(__name__)

_UPSERT_CHUNK = 500
_PAGE_SIZE = 1000


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except (ValueError, AttributeError):
            pass
    try:
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        if pd.isna(value):
            return None
    except TypeError:
        pass
    return value


def records_from_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """NaN은 NULL로 두고, date가 없는 행만 제외한다."""
    rows: list[dict[str, Any]] = []
    for raw in frame.to_dict(orient="records"):
        clean = {key: _json_safe(val) for key, val in raw.items()}
        if clean.get("date") is None:
            continue
        rows.append(clean)
    return rows


class DBClient:
    def __init__(self, url: str | None = None, key: str | None = None) -> None:
        self.url = config.require_env("SUPABASE_URL", url or config.SUPABASE_URL)
        self.key = config.require_env("SUPABASE_KEY", key or config.SUPABASE_KEY)
        self.client: Client = create_client(self.url, self.key)

    def upsert(self, table: str, records: list[dict[str, Any]], on_conflict: str = "date") -> int:
        if not records:
            logger.info("%s: 업서트할 행이 없습니다.", table)
            return 0

        written = 0
        for start in range(0, len(records), _UPSERT_CHUNK):
            chunk = records[start : start + _UPSERT_CHUNK]
            self.client.table(table).upsert(chunk, on_conflict=on_conflict).execute()
            written += len(chunk)
        logger.info("%s: %s행 업서트 완료", table, written)
        return written

    def fetch(
        self,
        table: str,
        *,
        columns: str = "*",
        order_by: str = "date",
        descending: bool = False,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """limit가 없으면 PostgREST 기본 1000행 제한을 넘겨 모두 가져온다."""
        if limit is not None:
            query = (
                self.client.table(table)
                .select(columns)
                .order(order_by, desc=descending)
                .limit(limit)
            )
            return list(query.execute().data or [])

        rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            query = (
                self.client.table(table)
                .select(columns)
                .order(order_by, desc=descending)
                .range(offset, offset + _PAGE_SIZE - 1)
            )
            page = list(query.execute().data or [])
            rows.extend(page)
            if len(page) < _PAGE_SIZE:
                break
            offset += _PAGE_SIZE
        return rows

    def fetch_frame(self, table: str, **kwargs: Any) -> pd.DataFrame:
        rows = self.fetch(table, **kwargs)
        if not rows:
            return pd.DataFrame()
        frame = pd.DataFrame(rows)
        if "date" in frame.columns:
            frame["date"] = pd.to_datetime(frame["date"])
        return frame

    def fetch_latest(self, table: str) -> dict[str, Any] | None:
        rows = self.fetch(table, order_by="date", descending=True, limit=1)
        return rows[0] if rows else None
