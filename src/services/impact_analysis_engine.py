"""Algorithmic analysis for completed market impact tracking sessions."""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class SeriesPoint:
    """Single observation for an asset during an event."""

    timestamp: datetime
    price: Optional[float]
    volume: Optional[float]
    source: Dict[str, Any]


class ImpactAnalysisEngine:
    """Derive quantitative insights from tracked market snapshots."""

    def __init__(self, *, outlier_threshold_pct: float = 2.5) -> None:
        # Percent threshold used when volatility is too low to determine outliers statistically.
        self.outlier_threshold_pct = abs(outlier_threshold_pct)

    def analyze_event(
        self,
        *,
        event_id: str,
        snapshots: Iterable[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Produce structured analytics for a completed tracking session."""
        ordered_snapshots = sorted(
            (self._normalize_snapshot(snapshot) for snapshot in snapshots),
            key=lambda entry: entry["captured_at"],
        )
        if not ordered_snapshots:
            return {
                "event_id": event_id,
                "generated_at": datetime.now(UTC),
                "metadata": metadata or {},
                "overview": {
                    "observation_count": 0,
                    "duration_seconds": 0,
                    "notes": "No snapshots available for analysis.",
                },
                "assets": {"crypto": {}, "indices": {}},
                "report": "No market data was captured for this event.",
            }

        crypto_stats = self._build_asset_statistics(
            ordered_snapshots, category="crypto"
        )
        index_stats = self._build_asset_statistics(
            ordered_snapshots, category="indices"
        )

        overview = self._build_overview(
            ordered_snapshots,
            crypto_stats=crypto_stats,
            index_stats=index_stats,
            metadata=metadata or {},
        )
        report = self._render_report(
            event_id=event_id,
            overview=overview,
            crypto_stats=crypto_stats,
            index_stats=index_stats,
        )

        return {
            "event_id": event_id,
            "generated_at": datetime.now(UTC),
            "metadata": metadata or {},
            "overview": overview,
            "assets": {
                "crypto": crypto_stats,
                "indices": index_stats,
            },
            "report": report,
        }

    def _normalize_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        captured_at = snapshot.get("captured_at")
        if isinstance(captured_at, datetime):
            timestamp = captured_at
        else:
            timestamp = datetime.now(UTC)

        return {
            "captured_at": timestamp,
            "sequence": snapshot.get("sequence", 0),
            "metadata": snapshot.get("metadata", {}) or {},
            "crypto": snapshot.get("crypto") or {},
            "indices": snapshot.get("indices") or {},
        }

    def _build_asset_statistics(
        self,
        snapshots: List[Dict[str, Any]],
        *,
        category: str,
    ) -> Dict[str, Any]:
        per_asset: Dict[str, List[SeriesPoint]] = {}

        for snapshot in snapshots:
            assets = snapshot.get(category, {}) or {}
            timestamp = snapshot["captured_at"]
            for symbol, payload in assets.items():
                price = payload.get("price")
                volume = payload.get("volume")
                if volume is None:
                    raw_payload = payload.get("raw")
                    if isinstance(raw_payload, dict):
                        volume = raw_payload.get("volume") or raw_payload.get("Volume")
                        if isinstance(volume, str):
                            try:
                                volume = float(volume.replace(",", ""))
                            except ValueError:
                                volume = None

                per_asset.setdefault(symbol, []).append(
                    SeriesPoint(
                        timestamp=timestamp,
                        price=price if isinstance(price, (int, float)) else None,
                        volume=volume if isinstance(volume, (int, float)) else None,
                        source=payload,
                    )
                )

        stats: Dict[str, Any] = {}
        for symbol, series in per_asset.items():
            stats[symbol] = self._compute_series_metrics(series)
        return stats

    def _compute_series_metrics(self, series: List[SeriesPoint]) -> Dict[str, Any]:
        clean_series = [point for point in series if point.price is not None]
        if not clean_series:
            return {
                "observations": len(series),
                "notes": "No price data captured.",
            }

        first = clean_series[0]
        last = clean_series[-1]
        high_point = max(clean_series, key=lambda p: p.price)
        low_point = min(clean_series, key=lambda p: p.price)

        absolute_change = last.price - first.price
        percent_change = self._safe_percent_change(last.price, first.price)
        cumulative_return = self._compute_cumulative_return(clean_series)

        returns = self._compute_step_returns(clean_series)
        volatility = statistics.pstdev(returns) if len(returns) > 1 else 0.0
        volatility_pct = volatility * 100 if volatility else 0.0

        drawdown = self._compute_max_drawdown(clean_series)
        outliers = self._detect_outliers(clean_series, returns, volatility)

        liquidity = self._compute_liquidity(series)

        trend = self._classify_trend(percent_change)

        return {
            "observations": len(clean_series),
            "first_observation": {
                "timestamp": first.timestamp,
                "price": first.price,
            },
            "last_observation": {
                "timestamp": last.timestamp,
                "price": last.price,
            },
            "change": {
                "absolute": absolute_change,
                "percent": percent_change,
                "cumulative_return": cumulative_return,
            },
            "high": {
                "timestamp": high_point.timestamp,
                "price": high_point.price,
            },
            "low": {
                "timestamp": low_point.timestamp,
                "price": low_point.price,
            },
            "volatility": {
                "step_standard_deviation": volatility,
                "percent": volatility_pct,
                "return_samples": len(returns),
            },
            "max_drawdown": drawdown,
            "trend": trend,
            "outliers": outliers,
            "liquidity": liquidity,
        }

    def _compute_cumulative_return(self, series: List[SeriesPoint]) -> Optional[float]:
        if len(series) < 2:
            return 0.0

        returns = []
        for prev, curr in zip(series, series[1:]):
            if (
                prev.price is None
                or curr.price is None
                or prev.price <= 0
                or curr.price <= 0
            ):
                continue
            returns.append(curr.price / prev.price - 1)

        if not returns:
            return 0.0

        cumulative = 1.0
        for step in returns:
            cumulative *= (1 + step)
        return cumulative - 1

    def _compute_step_returns(self, series: List[SeriesPoint]) -> List[float]:
        returns: List[float] = []
        for prev, curr in zip(series, series[1:]):
            if (
                prev.price is None
                or curr.price is None
                or prev.price <= 0
                or curr.price <= 0
            ):
                continue
            returns.append(math.log(curr.price / prev.price))
        return returns

    def _compute_liquidity(self, series: List[SeriesPoint]) -> Dict[str, Any]:
        volumes = [point.volume for point in series if point.volume is not None]
        if not volumes:
            return {
                "has_volume": False,
                "notes": "Volume data unavailable.",
            }

        avg_volume = sum(volumes) / len(volumes)
        volume_change = self._safe_percent_change(
            volumes[-1],
            volumes[0],
        )
        return {
            "has_volume": True,
            "average": avg_volume,
            "change_percent": volume_change,
        }

    def _compute_max_drawdown(self, series: List[SeriesPoint]) -> Dict[str, Any]:
        running_peak = series[0]
        max_drawdown = 0.0
        trough_point = series[0]

        for point in series[1:]:
            if point.price is None:
                continue
            if point.price > running_peak.price:
                running_peak = point
                continue

            drawdown = self._safe_percent_change(point.price, running_peak.price)
            if drawdown < max_drawdown:
                max_drawdown = drawdown
                trough_point = point

        if max_drawdown == 0.0:
            return {
                "percent": 0.0,
                "from_timestamp": running_peak.timestamp,
                "to_timestamp": running_peak.timestamp,
            }

        return {
            "percent": max_drawdown,
            "from_timestamp": running_peak.timestamp,
            "to_timestamp": trough_point.timestamp,
            "from_price": running_peak.price,
            "to_price": trough_point.price,
        }

    def _detect_outliers(
        self,
        series: List[SeriesPoint],
        log_returns: List[float],
        volatility: float,
    ) -> List[Dict[str, Any]]:
        if not log_returns:
            return []

        threshold = max(
            self.outlier_threshold_pct / 100.0,
            3 * volatility if volatility else 0.0,
        )

        outliers: List[Dict[str, Any]] = []
        for (prev, curr), step_return in zip(
            zip(series, series[1:]),
            log_returns,
        ):
            percent_move = math.expm1(step_return) * 100.0
            if abs(step_return) >= threshold:
                outliers.append(
                    {
                        "timestamp": curr.timestamp,
                        "percent_move": percent_move,
                        "price": curr.price,
                        "threshold_percent": threshold * 100.0,
                        "from_price": prev.price,
                    }
                )
        return outliers

    def _classify_trend(self, percent_change: Optional[float]) -> Dict[str, Any]:
        if percent_change is None:
            return {"direction": "unknown", "confidence": 0.0}

        magnitude = abs(percent_change)
        if percent_change > 0:
            direction = "uptrend"
        elif percent_change < 0:
            direction = "downtrend"
        else:
            direction = "flat"

        if magnitude >= 5:
            confidence = 0.9
        elif magnitude >= 2:
            confidence = 0.7
        elif magnitude >= 1:
            confidence = 0.5
        else:
            confidence = 0.3

        return {
            "direction": direction,
            "confidence": confidence,
            "magnitude_percent": percent_change,
        }

    def _build_overview(
        self,
        snapshots: List[Dict[str, Any]],
        *,
        crypto_stats: Dict[str, Any],
        index_stats: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        start = snapshots[0]["captured_at"]
        end = snapshots[-1]["captured_at"]
        duration = (end - start).total_seconds()

        movers = self._identify_top_movers(crypto_stats, index_stats)
        return {
            "observation_count": len(snapshots),
            "window": {
                "start": start,
                "end": end,
                "duration_seconds": duration,
            },
            "movers": movers,
            "metadata": metadata,
        }

    def _identify_top_movers(
        self,
        crypto_stats: Dict[str, Any],
        index_stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        movers: Dict[str, Any] = {}

        for category_name, stats in (("crypto", crypto_stats), ("indices", index_stats)):
            if not stats:
                movers[category_name] = None
                continue

            top_symbol, top_stat = max(
                stats.items(),
                key=lambda item: abs(item[1].get("change", {}).get("percent") or 0),
            )
            movers[category_name] = {
                "symbol": top_symbol,
                "percent_change": top_stat["change"].get("percent"),
                "trend": top_stat.get("trend"),
            }

        return movers

    def _render_report(
        self,
        *,
        event_id: str,
        overview: Dict[str, Any],
        crypto_stats: Dict[str, Any],
        index_stats: Dict[str, Any],
    ) -> str:
        lines: List[str] = []
        window = overview["window"]
        lines.append(f"Event Impact Report — {event_id}")
        lines.append(
            f"Window: {window['start'].isoformat()} → {window['end'].isoformat()} "
            f"({window['duration_seconds'] / 60:.1f} min, {overview['observation_count']} samples)"
        )

        def append_section(title: str, stats: Dict[str, Any]) -> None:
            if not stats:
                lines.append(f"{title}: keine Messwerte erfasst.")
                return
            lines.append(title + ":")
            for symbol, data in stats.items():
                change = data["change"]
                trend = data.get("trend", {})
                direction = trend.get("direction", "unbekannt")
                magnitude = change.get("percent")
                lines.append(
                    f"  • {symbol.upper()}: {magnitude:+.2f}% "
                    f"(High {data['high']['price']:.2f} @ {data['high']['timestamp'].isoformat()}, "
                    f"Low {data['low']['price']:.2f} @ {data['low']['timestamp'].isoformat()}, "
                    f"Trend: {direction})"
                )
                if data.get("outliers"):
                    lines.append(
                        f"    ↳ Ausreißer: {len(data['outliers'])} Bewegungen > "
                        f"{data['outliers'][0]['threshold_percent']:.2f}%"
                    )

        append_section("Kryptowerte", crypto_stats)
        append_section("Indizes", index_stats)
        return "\n".join(lines)

    def _safe_percent_change(
        self,
        current: Optional[float],
        base: Optional[float],
    ) -> Optional[float]:
        if current is None or base in (None, 0):
            return None
        return ((current - base) / base) * 100.0
