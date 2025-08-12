from __future__ import annotations

import argparse
from typing import Dict

import pandas as pd

from config import get_config
from data_fetchers import download_market_data
from news import get_news_for_symbols
from sentiment import score_by_symbol
from analytics import build_summaries, investment_suggestions


def main():
    parser = argparse.ArgumentParser(description="Idées d'investissement basées sur règles simplistes.")
    parser.add_argument("--asset-class", default="equities", help="equities|etf|crypto|indices|commodities|forex|bonds")
    parser.add_argument("--period", default=None, help="Période yfinance (ex: 1y, 2y)")
    parser.add_argument("--interval", default=None, help="Interval yfinance (ex: 1d, 1wk)")
    parser.add_argument("--top-n", type=int, default=10)
    args = parser.parse_args()

    cfg = get_config()
    period = args.period or cfg.default_period
    interval = args.interval or cfg.default_interval

    symbols = cfg.universes.get(args.asset_class, [])
    if not symbols:
        raise SystemExit(f"Classe d'actifs inconnue: {args.asset_class}")

    data = download_market_data(symbols, period=period, interval=interval)
    news = get_news_for_symbols(list(data.keys()), newsapi_key=cfg.newsapi_key)
    sentiment = score_by_symbol(news)

    summaries = build_summaries(data, news_sentiment_by_symbol=sentiment, fmp_api_key=cfg.fmp_api_key)
    ideas = investment_suggestions(summaries, top_n=args.top_n)

    print("Suggestions d'investissement:")
    for s, score, rationale in ideas:
        sent = f"sent={s.news_sentiment:.3f}" if s.news_sentiment else "sent=0"
        earn = (
            f"earn={s.earnings_surprise:.3f}" if s.earnings_surprise is not None else "earn=?"
        )
        print(f"- {s.symbol}: score={score:.3f} ({sent}, {earn}) | {rationale}")


if __name__ == "__main__":
    main()