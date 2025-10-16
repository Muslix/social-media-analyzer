#!/usr/bin/env python3
"""
Backtesting script for high-urgency LLM events.

For each entry in the LLM training data flagged with urgency 'immediate' or
'hours', fetch post-event crypto and index prices and compute simple metrics
for 6h and 12h windows.
"""
from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import sys

# Ensure local src package is importable when running as a script
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import Config
from src.services.historical_data import (
    BinanceHistoricalClient,
    CoinGeckoHistoricalClient,
    HistoricalDataError,
    YahooFinanceHistoricalClient,
    nearest_price,
    window_slice,
)
from src.utils.rate_limiter import RateLimiter

SUPPORTED_URGENCIES = {"immediate", "hours"}
WINDOWS = {
    "6h": timedelta(hours=6),
    "12h": timedelta(hours=12),
}
PRE_EVENT_MARGIN = timedelta(minutes=15)

logger = logging.getLogger("backtest")


BINANCE_SYMBOL_OVERRIDES = {
    "btc": "BTCUSDT",
    "eth": "ETHUSDT",
    "ada": "ADAUSDT",
    "sol": "SOLUSDT",
}


def resolve_binance_pair(symbol: str) -> str:
    """Map internal symbol to a Binance trading pair (defaults to USDT)."""
    return BINANCE_SYMBOL_OVERRIDES.get(symbol.lower(), f"{symbol.upper()}USDT")


@dataclass
class EventRecord:
    timestamp: datetime
    urgency: str
    keyword_score: int
    llm_score: int
    post_text: str
    raw: Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("training_data/llm_training_data.jsonl"),
        help="Path to the JSONL file with LLM analysis training data.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("training_data/backtest_results.jsonl"),
        help="Optional destination for JSONL output (append mode).",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="Limit the number of events processed (for debugging).",
    )
    parser.add_argument(
        "--skip-crypto",
        action="store_true",
        help="Skip crypto lookups (useful when provider API is unavailable).",
    )
    parser.add_argument(
        "--skip-indices",
        action="store_true",
        help="Skip index lookups (useful when Yahoo API is unavailable).",
    )
    parser.add_argument(
        "--crypto-provider",
        choices=["binance", "coingecko"],
        default="coingecko",
        help="Which provider to use for crypto history (default: coingecko).",
    )
    parser.add_argument(
        "--crypto-delay",
        type=float,
        default=10.0,
        help="Minimum delay in seconds between crypto requests (default: 10.0).",
    )
    parser.add_argument(
        "--yahoo-delay",
        type=float,
        default=10.0,
        help="Minimum delay in seconds between Yahoo Finance requests (default: 10.0).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: INFO).",
    )
    return parser.parse_args()


def load_events(path: Path, *, limit: Optional[int] = None) -> List[EventRecord]:
    events: List[EventRecord] = []
    if not path.exists():
        raise FileNotFoundError(f"Training data not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("Skipping invalid JSON line in %s", path)
                continue

            urgency = (record.get("urgency") or "").lower()
            if urgency not in SUPPORTED_URGENCIES:
                continue

            timestamp_raw = record.get("timestamp")
            if not timestamp_raw:
                continue
            try:
                timestamp = datetime.fromisoformat(timestamp_raw)
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
            except ValueError:
                logger.warning("Invalid timestamp %s, skipping entry", timestamp_raw)
                continue

            events.append(
                EventRecord(
                    timestamp=timestamp,
                    urgency=urgency,
                    keyword_score=int(record.get("keyword_score") or 0),
                    llm_score=int(record.get("llm_score") or 0),
                    post_text=(record.get("post_text") or "")[:500],
                    raw=record,
                )
            )

            if limit and len(events) >= limit:
                break

    return events


def analyse_series(
    series: Iterable[Tuple[datetime, float]],
    *,
    baseline: datetime,
) -> Dict[str, object]:
    data = list(series)
    data.sort(key=lambda item: item[0])

    base_price = nearest_price(data, baseline, forward_only=False)
    result: Dict[str, object] = {
        "base_price": base_price,
        "windows": {},
        "samples": len(data),
    }
    if base_price is None or not data:
        return result

    for label, delta in WINDOWS.items():
        window_end = baseline + delta
        price_at_end = nearest_price(data, window_end, forward_only=True)
        window_points = window_slice(data, baseline, window_end)
        if not window_points or price_at_end is None:
            result["windows"][label] = {
                "price": price_at_end,
                "abs_change": None,
                "pct_change": None,
                "high": None,
                "low": None,
                "high_time": None,
                "low_time": None,
                "samples": len(window_points),
            }
            continue

        high_ts, high_price = max(window_points, key=lambda item: item[1])
        low_ts, low_price = min(window_points, key=lambda item: item[1])
        abs_change = price_at_end - base_price
        pct_change = (abs_change / base_price) * 100 if base_price else None

        result["windows"][label] = {
            "price": price_at_end,
            "abs_change": abs_change,
            "pct_change": pct_change,
            "high": high_price,
            "low": low_price,
            "high_time": high_ts.isoformat(),
            "low_time": low_ts.isoformat(),
            "samples": len(window_points),
        }

    return result


def serialize_for_json(data: Dict[str, object]) -> Dict[str, object]:
    """Ensure datetime objects are serialized as ISO strings."""
    serialised: Dict[str, object] = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            serialised[key] = value.isoformat()
        elif isinstance(value, dict):
            serialised[key] = serialize_for_json(value)  # type: ignore[arg-type]
        elif isinstance(value, list):
            serialised[key] = [
                serialize_for_json(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            serialised[key] = value
    return serialised


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    config = Config()

    crypto_mapping = config.MARKET_IMPACT_CRYPTO_IDS
    index_mapping = config.MARKET_IMPACT_INDEX_IDS

    events = load_events(args.input, limit=args.max_events)
    if not events:
        logger.warning("No matching events found in %s", args.input)
        return 1

    logger.info("Loaded %s events for backtesting", len(events))

    crypto_provider = args.crypto_provider.lower()
    crypto_limiter = RateLimiter(min_interval_seconds=args.crypto_delay)
    yahoo_limiter = RateLimiter(min_interval_seconds=args.yahoo_delay)

    crypto_client = (
        None
        if args.skip_crypto
        else (
            CoinGeckoHistoricalClient(
                vs_currency=config.MARKET_IMPACT_FIAT,
                rate_limiter=crypto_limiter,
            )
            if crypto_provider == "coingecko"
            else BinanceHistoricalClient(rate_limiter=crypto_limiter)
        )
    )
    index_client = (
        None
        if args.skip_indices
        else YahooFinanceHistoricalClient(rate_limiter=yahoo_limiter)
    )

    longest_window = max(WINDOWS.values())
    results: List[Dict[str, object]] = []

    for idx, event in enumerate(events, start=1):
        logger.info(
            "[%s/%s] Processing event at %s (urgency=%s, score=%s)",
            idx,
            len(events),
            event.timestamp.isoformat(),
            event.urgency,
            event.llm_score,
        )

        window_end = event.timestamp + longest_window
        window_start = event.timestamp - PRE_EVENT_MARGIN

        event_result: Dict[str, object] = {
            "event_timestamp": event.timestamp.isoformat(),
            "urgency": event.urgency,
            "keyword_score": event.keyword_score,
            "llm_score": event.llm_score,
            "post_excerpt": event.post_text.strip().replace("\n", " ")[:280],
            "assets": {
                "crypto": {},
                "indices": {},
            },
        }

        if crypto_client:
            for symbol, identifier in crypto_mapping.items():
                try:
                    if crypto_provider == "coingecko":
                        series = crypto_client.fetch_range(  # type: ignore[call-arg]
                            coin_id=identifier,
                            start=window_start,
                            end=window_end,
                        )
                    else:
                        pair = resolve_binance_pair(symbol)
                        series = crypto_client.fetch_range(  # type: ignore[call-arg]
                            symbol_pair=pair,
                            start=window_start,
                            end=window_end,
                        )
                except HistoricalDataError as exc:
                    label = identifier if crypto_provider == "coingecko" else pair
                    logger.warning("Crypto fetch failed for %s (%s): %s", symbol, label, exc)
                    event_result["assets"]["crypto"][symbol] = {
                        "error": str(exc),
                    }
                    continue

                metrics = analyse_series(series, baseline=event.timestamp)
                event_result["assets"]["crypto"][symbol] = metrics

        if index_client:
            for alias, yahoo_symbol in index_mapping.items():
                try:
                    series = index_client.fetch_range(
                        symbol=yahoo_symbol,
                        start=window_start,
                        end=window_end,
                        interval="1h",
                    )
                except HistoricalDataError as exc:
                    logger.warning("Index fetch failed for %s (%s): %s", alias, yahoo_symbol, exc)
                    event_result["assets"]["indices"][alias] = {
                        "error": str(exc),
                    }
                    continue

                metrics = analyse_series(series, baseline=event.timestamp)
                event_result["assets"]["indices"][alias] = metrics

        results.append(event_result)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("a", encoding="utf-8") as handle:
            for item in results:
                json.dump(item, handle, ensure_ascii=False)
                handle.write("\n")
        logger.info("Appended %s backtest results to %s", len(results), args.output)

    # Print concise summary to console
    for item in results:
        logger.info(
            "Event %s | urgency=%s | crypto=%s | indices=%s",
            item["event_timestamp"],
            item["urgency"],
            list(item["assets"]["crypto"].keys()),
            list(item["assets"]["indices"].keys()),
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
