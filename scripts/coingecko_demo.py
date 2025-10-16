#!/usr/bin/env python3
"""
Mini CoinGecko demo script.

Run after installing pycoingecko:
    pip install pycoingecko
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from pycoingecko import CoinGeckoAPI


def print_header(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def show_current_prices(cg: CoinGeckoAPI, coins: Iterable[str], vs: str = "usd") -> None:
    print_header(f"Current prices ({vs.upper()})")
    prices = cg.get_price(ids=",".join(coins), vs_currencies=vs)
    for coin in coins:
        price = prices.get(coin, {}).get(vs)
        if price is None:
            print(f"{coin}: unavailable")
        else:
            print(f"{coin:<12} -> {price:.2f} {vs.upper()}")


def show_top_market_coins(cg: CoinGeckoAPI, *, limit: int = 5, vs: str = "usd") -> None:
    print_header(f"Top {limit} coins by market cap ({vs.upper()})")
    market_data = cg.get_coins_markets(vs_currency=vs, per_page=limit, page=1, order="market_cap_desc")
    for coin in market_data:
        name = coin["name"]
        symbol = coin["symbol"].upper()
        price = coin["current_price"]
        market_cap = coin["market_cap"]
        change = coin["price_change_percentage_24h"]
        print(f"{name} ({symbol})  price: {price:,.2f} {vs.upper()}  cap: {market_cap:,.0f}  24h: {change:+.2f}%")


def show_recent_history(cg: CoinGeckoAPI, coin_id: str, *, days: int = 7, vs: str = "usd") -> None:
    print_header(f"{coin_id} last {days} days (daily close, {vs.upper()})")
    history = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency=vs, days=days)
    for timestamp_ms, price in history.get("prices", []):
        ts = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        print(f"{ts.isoformat()} -> {price:,.2f} {vs.upper()}")


def main() -> None:
    try:
        cg = CoinGeckoAPI()
    except Exception as exc:  # pragma: no cover - pycoingecko import/runtime issues
        raise SystemExit(f"Failed to initialise CoinGecko client: {exc}") from exc

    try:
        show_current_prices(cg, ["bitcoin", "ethereum", "solana"])
        show_top_market_coins(cg, limit=5)
        show_recent_history(cg, "bitcoin", days=7)
    except Exception as exc:  # pragma: no cover - network/API issues
        raise SystemExit(f"CoinGecko request failed: {exc}") from exc


if __name__ == "__main__":
    main()
