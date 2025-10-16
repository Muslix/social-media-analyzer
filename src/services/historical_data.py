"""Utilities for fetching historical market data for backtesting."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import quote

import requests

from src.utils.rate_limiter import RateLimiter

try:
    from pycoingecko import CoinGeckoAPI
except ImportError:  # pragma: no cover - optional dependency
    CoinGeckoAPI = None
logger = logging.getLogger(__name__)


class HistoricalDataError(RuntimeError):
    """Raised when a historical price provider fails."""


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class CoinGeckoHistoricalClient:
    """Fetch crypto price history from CoinGecko."""

    def __init__(
        self,
        *,
        vs_currency: str = "usd",
        session: Optional[requests.Session] = None,
        timeout_seconds: int = 15,
        rate_limiter: Optional[RateLimiter] = None,
        client: Optional["CoinGeckoAPI"] = None,
    ) -> None:
        self.vs_currency = vs_currency
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self.rate_limiter = rate_limiter
        if client is not None:
            self.client = client
        else:
            if CoinGeckoAPI is None:
                raise RuntimeError(
                    "pycoingecko is required for CoinGeckoHistoricalClient. "
                    "Install with 'pip install pycoingecko'."
                )
            self.client = CoinGeckoAPI()

    def fetch_range(
        self,
        *,
        coin_id: str,
        start: datetime,
        end: datetime,
    ) -> List[Tuple[datetime, float]]:
        """
        Fetch price ticks between start and end (inclusive).

        Returns list of (timestamp, price) sorted ascending.
        """
        start_utc = _ensure_utc(start)
        end_utc = _ensure_utc(end)

        try:
            if self.rate_limiter:
                self.rate_limiter.wait()
            payload = self.client.get_coin_market_chart_range_by_id(
                id=coin_id,
                vs_currency=self.vs_currency,
                from_timestamp=int(start_utc.timestamp()),
                to_timestamp=int(end_utc.timestamp()),
            )
        except Exception as exc:  # pragma: no cover - network/dependency issues
            raise HistoricalDataError(f"CoinGecko request failed: {exc}") from exc

        prices = (payload or {}).get("prices") or []
        series: List[Tuple[datetime, float]] = []
        for entry in prices:
            if not isinstance(entry, Sequence) or len(entry) < 2:
                continue
            timestamp_ms, price = entry[0], entry[1]
            try:
                ts = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                price_value = float(price)
            except (ValueError, TypeError):
                continue
            series.append((ts, price_value))

        series.sort(key=lambda item: item[0])
        return series


class BinanceHistoricalClient:
    """Fetch crypto price history from Binance spot market (USDT pairs)."""

    API_URL = "https://api.binance.com/api/v3/klines"

    def __init__(
        self,
        *,
        interval: str = "5m",
        session: Optional[requests.Session] = None,
        timeout_seconds: int = 15,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        self.interval = interval
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self.rate_limiter = rate_limiter

    def fetch_range(
        self,
        *,
        symbol_pair: str,
        start: datetime,
        end: datetime,
    ) -> List[Tuple[datetime, float]]:
        """
        Fetch closing prices between start and end inclusive for a Binance pair.
        """
        start_utc = _ensure_utc(start)
        end_utc = _ensure_utc(end)

        params = {
            "symbol": symbol_pair.upper(),
            "interval": self.interval,
            "startTime": int(start_utc.timestamp() * 1000),
            "endTime": int(end_utc.timestamp() * 1000),
            "limit": 1000,
        }

        try:
            if self.rate_limiter:
                self.rate_limiter.wait()
            response = self.session.get(self.API_URL, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:  # pragma: no cover - network dependent
            raise HistoricalDataError(f"Binance request failed: {exc}") from exc
        except ValueError as exc:  # pragma: no cover - bad JSON
            raise HistoricalDataError(f"Binance returned invalid JSON: {exc}") from exc

        if not isinstance(payload, list):
            raise HistoricalDataError(f"Unexpected Binance response for {symbol_pair}")

        series: List[Tuple[datetime, float]] = []
        for entry in payload:
            if not isinstance(entry, Sequence) or len(entry) < 5:
                continue
            open_time_ms = entry[0]
            close_price = entry[4]
            try:
                ts = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc)
                price_value = float(close_price)
            except (ValueError, TypeError):
                continue
            if ts < start_utc or ts > end_utc:
                continue
            series.append((ts, price_value))

        series.sort(key=lambda item: item[0])
        return series


class YahooFinanceHistoricalClient:
    """Fetch index (and equity) price history from Yahoo Finance chart API."""

    API_TEMPLATE = (
        "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        "?period1={period1}&period2={period2}&interval={interval}&includePrePost=true"
    )

    def __init__(
        self,
        *,
        session: Optional[requests.Session] = None,
        timeout_seconds: int = 15,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self.rate_limiter = rate_limiter

    def fetch_range(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1h",
    ) -> List[Tuple[datetime, float]]:
        """
        Fetch price ticks between start and end (inclusive) for a Yahoo symbol.
        Returns list of (timestamp, price) sorted ascending.
        """
        start_utc = _ensure_utc(start)
        end_utc = _ensure_utc(end)

        url = self.API_TEMPLATE.format(
            symbol=quote(symbol, safe=""),
            period1=int(start_utc.timestamp()),
            period2=int(end_utc.timestamp()),
            interval=interval,
        )

        try:
            if self.rate_limiter:
                self.rate_limiter.wait()
            response = self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:  # pragma: no cover - network dependent
            raise HistoricalDataError(f"Yahoo Finance request failed: {exc}") from exc
        except ValueError as exc:  # pragma: no cover - invalid JSON
            raise HistoricalDataError(f"Yahoo Finance returned invalid JSON: {exc}") from exc

        chart = (payload or {}).get("chart", {})
        error = chart.get("error")
        if error:
            raise HistoricalDataError(
                f"Yahoo Finance returned error for {symbol}: {error.get('description')}"
            )

        result = chart.get("result")
        if not result:
            return []

        data = result[0]
        timestamps = data.get("timestamp") or []
        indicators = (data.get("indicators") or {}).get("adjclose") or []
        closes = indicators[0].get("adjclose") if indicators else None
        if closes is None:
            return []

        series: List[Tuple[datetime, float]] = []
        for ts_raw, price in zip(timestamps, closes):
            if ts_raw is None or price is None:
                continue
            try:
                ts = datetime.fromtimestamp(int(ts_raw), tz=timezone.utc)
                price_value = float(price)
            except (ValueError, TypeError):
                continue
            if start_utc <= ts <= end_utc:
                series.append((ts, price_value))

        series.sort(key=lambda item: item[0])
        return series


def nearest_price(
    series: Iterable[Tuple[datetime, float]],
    target: datetime,
    *,
    forward_only: bool = True,
) -> Optional[float]:
    """
    Return the price closest to the target timestamp.

    If `forward_only` is True, prefer the first data point at or after the target.
    Falls back to the latest available price before the target if no forward point exists.
    """
    target_utc = _ensure_utc(target)
    series_list = list(series)
    if not series_list:
        return None

    forward_candidates = [
        price for ts, price in series_list if ts >= target_utc
    ]
    if forward_candidates:
        return forward_candidates[0]

    if forward_only:
        return None

    backward_candidates = [
        price for ts, price in reversed(series_list) if ts <= target_utc
    ]
    return backward_candidates[0] if backward_candidates else None


def window_slice(
    series: Iterable[Tuple[datetime, float]],
    start: datetime,
    end: datetime,
) -> List[Tuple[datetime, float]]:
    """Return subsequence of points inside the inclusive [start, end] window."""
    start_utc = _ensure_utc(start)
    end_utc = _ensure_utc(end)
    return [
        (ts, price)
        for ts, price in series
        if start_utc <= ts <= end_utc
    ]
