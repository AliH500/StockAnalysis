"""
yfinance-backed loader for the Stock Analysis GUI.

Returns 1-week, 1-minute close-price data with timestamps in the system's
local timezone. Fixes the original-CLI bug where the index was converted
to UTC and then `tz_localize(None)`'d, leaving naive-UTC datetimes that
the user silently misread as local wall-clock time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo

import yfinance as yf


@dataclass(frozen=True)
class StockSeries:
    """Tz-aware 1-minute close-price series for a single ticker."""

    ticker: str
    # Tz-aware datetimes in the system's local zone. Index-aligned with `closes`.
    timestamps: list[datetime]
    closes: list[float]
    # String repr of the local zone (IANA name when available, else fixed offset).
    local_tz: str


def _system_local_tz() -> tzinfo:
    """System's local tzinfo via stdlib — no extra dependency."""
    # `datetime.now().astimezone()` resolves the OS local zone. The tzinfo
    # is a `zoneinfo.ZoneInfo` on most modern Linux installs and a fixed
    # offset when no IANA zone is discoverable; both work for `tz_convert`.
    local = datetime.now().astimezone().tzinfo
    assert local is not None  # astimezone() always attaches a tzinfo
    return local


def fetch_series(ticker: str) -> StockSeries:
    """
    Fetch the last 7 days of 1-minute close prices for `ticker`, returned
    with the timestamp index converted to the system's local timezone.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("Ticker is empty.")

    end = datetime.now()
    start = end - timedelta(days=7)
    df = yf.Ticker(ticker).history(start=start, end=end, interval="1m")
    if df.empty:
        raise ValueError(f"No data returned for {ticker!r}.")

    local_tz = _system_local_tz()
    # yfinance returns tz-aware intraday indices; guard the naive case anyway.
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert(local_tz)

    timestamps = [ts.to_pydatetime() for ts in df.index]
    closes = [float(v) for v in df["Close"].values]

    return StockSeries(
        ticker=ticker,
        timestamps=timestamps,
        closes=closes,
        local_tz=str(local_tz),
    )
