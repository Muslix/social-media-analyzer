#!/usr/bin/env python3
"""
Analyze backtest results and extract aggregated insights.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


WINDOW_CHOICES = {"6h", "12h"}


@dataclass
class WindowMetrics:
    percent_change: float
    abs_change: float
    price: float
    high: float
    low: float
    high_time: Optional[str]
    low_time: Optional[str]


@dataclass
class AssetObservation:
    event_ts: str
    urgency: str
    asset_type: str
    asset_name: str
    window: str
    metrics: WindowMetrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("training_data/backtest_results.jsonl"),
        help="Path to the JSONL file produced by backtest_market_impact.py",
    )
    parser.add_argument(
        "--window",
        choices=sorted(WINDOW_CHOICES),
        default="6h",
        help="Select which window (6h or 12h) to analyze",
    )
    parser.add_argument(
        "--min-abs-move",
        type=float,
        default=0.5,
        help="Only include observations where |pct_change| >= threshold (default: 0.5)",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="Limit the number of events processed (after filtering by window)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary instead of human-friendly text",
    )
    return parser.parse_args()


def load_backtest_results(
    path: Path,
    *,
    window: str,
    min_abs_move: float,
    max_events: Optional[int] = None,
) -> List[AssetObservation]:
    if not path.exists():
        raise FileNotFoundError(f"Backtest results not found: {path}")

    observations: List[AssetObservation] = []
    events_count = 0

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_ts = event.get("event_timestamp")
            urgency = event.get("urgency", "unknown")
            assets = event.get("assets") or {}

            relevant_observations = extract_observations(event_ts, urgency, assets, window)
            filtered = [
                obs
                for obs in relevant_observations
                if math.fabs(obs.metrics.percent_change) >= min_abs_move
            ]

            if filtered:
                observations.extend(filtered)
                events_count += 1
                if max_events and events_count >= max_events:
                    break

    return observations


def extract_observations(
    event_ts: Optional[str],
    urgency: str,
    assets: Dict[str, Dict[str, Dict[str, object]]],
    window: str,
) -> List[AssetObservation]:
    observations: List[AssetObservation] = []

    for asset_type, entries in assets.items():
        for asset_name, metrics in entries.items():
            if "error" in metrics:
                continue

            windows = metrics.get("windows") if isinstance(metrics, dict) else None
            if not isinstance(windows, dict):
                continue
            window_data = windows.get(window)
            if not isinstance(window_data, dict):
                continue

            pct_change = window_data.get("pct_change")
            abs_change = window_data.get("abs_change")
            price = window_data.get("price")

            if not all(
                isinstance(value, (int, float))
                for value in (pct_change, abs_change, price)
            ):
                continue

            observations.append(
                AssetObservation(
                    event_ts=event_ts or "unknown",
                    urgency=urgency,
                    asset_type=asset_type,
                    asset_name=asset_name,
                    window=window,
                    metrics=WindowMetrics(
                        percent_change=float(pct_change),
                        abs_change=float(abs_change),
                        price=float(price),
                        high=float(window_data.get("high") or price),
                        low=float(window_data.get("low") or price),
                        high_time=window_data.get("high_time"),
                        low_time=window_data.get("low_time"),
                    ),
                )
            )
    return observations


def aggregate_by_asset(observations: Iterable[AssetObservation]) -> Dict[str, Dict[str, float]]:
    data: Dict[str, List[float]] = {}

    for obs in observations:
        key = f"{obs.asset_type}:{obs.asset_name}"
        data.setdefault(key, []).append(obs.metrics.percent_change)

    aggregates: Dict[str, Dict[str, float]] = {}
    for asset_key, values in data.items():
        aggregates[asset_key] = {
            "count": len(values),
            "avg_pct": statistics.mean(values),
            "median_pct": statistics.median(values),
            "max_pct": max(values),
            "min_pct": min(values),
        }
    return aggregates


def summarize_events(observations: Iterable[AssetObservation]) -> List[Dict[str, object]]:
    events: Dict[str, List[AssetObservation]] = {}
    for obs in observations:
        events.setdefault(obs.event_ts, []).append(obs)

    summaries: List[Dict[str, object]] = []
    for event_ts, event_observations in sorted(events.items()):
        strongest = max(event_observations, key=lambda obs: abs(obs.metrics.percent_change))
        summaries.append(
            {
                "event_timestamp": event_ts,
                "urgency": strongest.urgency,
                "asset": strongest.asset_name.upper(),
                "asset_type": strongest.asset_type,
                "window": strongest.window,
                "move_pct": strongest.metrics.percent_change,
                "high_time": strongest.metrics.high_time,
                "low_time": strongest.metrics.low_time,
            }
        )
    return summaries


def print_human_readable(
    observations: List[AssetObservation],
    aggregates: Dict[str, Dict[str, float]],
    summaries: List[Dict[str, object]],
    *,
    window: str,
    threshold: float,
) -> None:
    if not observations:
        print("Keine passenden Beobachtungen gefunden.")
        return

    print(f"Analyse-Fenster: {window} | Schwelle: ±{threshold:.2f}% | Beobachtungen: {len(observations)}")
    print("\nTop Ereignisse:")
    for summary in summaries:
        move_pct = summary["move_pct"]
        direction = "▲" if move_pct >= 0 else "▼"
        print(
            f"- {summary['event_timestamp']} ({summary['urgency']}): "
            f"{summary['asset_type']} {summary['asset']} {direction} {move_pct:+.2f}%"
        )

    print("\nAggregierte Performance je Asset:")
    for asset_key, stats in sorted(aggregates.items()):
        direction = "▲" if stats["avg_pct"] >= 0 else "▼"
        print(
            f"- {asset_key}: n={stats['count']} "
            f"avg={stats['avg_pct']:+.2f}% "
            f"median={stats['median_pct']:+.2f}% "
            f"span=({stats['min_pct']:+.2f}%, {stats['max_pct']:+.2f}%) {direction}"
        )


def emit_json_summary(
    observations: List[AssetObservation],
    aggregates: Dict[str, Dict[str, float]],
    summaries: List[Dict[str, object]],
) -> None:
    payload = {
        "count": len(observations),
        "asset_summaries": aggregates,
        "event_summaries": summaries,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()

    observations = load_backtest_results(
        args.input,
        window=args.window,
        min_abs_move=args.min_abs_move,
        max_events=args.max_events,
    )

    aggregates = aggregate_by_asset(observations)
    summaries = summarize_events(observations)

    if args.json:
        emit_json_summary(observations, aggregates, summaries)
    else:
        print_human_readable(observations, aggregates, summaries, window=args.window, threshold=args.min_abs_move)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
