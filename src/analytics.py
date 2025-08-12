from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

from data_fetchers import summarize_ticker
from earnings import get_last_earnings_surprise


@dataclass
class TickerSummary:
    symbol: str
    last: float
    day_chg: float
    last_52w_high: float
    last_52w_low: float
    dist_to_high: float
    dist_to_low: float
    month_ret_sum: float
    news_sentiment: float = 0.0
    earnings_surprise: Optional[float] = None


def build_summaries(
    data_by_ticker: Dict[str, pd.DataFrame],
    news_sentiment_by_symbol: Optional[Dict[str, float]] = None,
    fmp_api_key: Optional[str] = None,
) -> List[TickerSummary]:
    summaries: List[TickerSummary] = []
    for sym, df in data_by_ticker.items():
        try:
            s = summarize_ticker(df)
        except Exception:
            continue
        sentiment = 0.0
        if news_sentiment_by_symbol and sym in news_sentiment_by_symbol:
            sentiment = float(news_sentiment_by_symbol[sym])
        earnings_surprise = None
        if sym.isalpha():
            earnings_surprise = get_last_earnings_surprise(sym, fmp_api_key)
        summaries.append(
            TickerSummary(
                symbol=sym,
                last=s["last"],
                day_chg=s["day_chg"],
                last_52w_high=s["last_52w_high"],
                last_52w_low=s["last_52w_low"],
                dist_to_high=s["dist_to_high"],
                dist_to_low=s["dist_to_low"],
                month_ret_sum=s["month_ret_sum"],
                news_sentiment=sentiment,
                earnings_surprise=earnings_surprise,
            )
        )
    return summaries


def top_gainers_losers(summaries: List[TickerSummary], top_n: int = 10) -> Tuple[List[TickerSummary], List[TickerSummary]]:
    ordered = sorted(summaries, key=lambda x: x.day_chg, reverse=True)
    return ordered[:top_n], ordered[-top_n:][::-1]


def top_52w_highs_lows(summaries: List[TickerSummary], top_n: int = 10) -> Tuple[List[TickerSummary], List[TickerSummary]]:
    highs = sorted(summaries, key=lambda x: x.dist_to_high)
    lows = sorted(summaries, key=lambda x: x.dist_to_low)
    return highs[:top_n], lows[:top_n]


def investment_suggestions(summaries: List[TickerSummary], top_n: int = 10) -> List[Tuple[TickerSummary, float, str]]:
    scored: List[Tuple[TickerSummary, float, str]] = []
    for s in summaries:
        score = 0.0
        rationale = []
        if s.month_ret_sum > 0:
            score += min(s.month_ret_sum, 0.2) * 2.0
            rationale.append("Momentum 1M positif")
        else:
            score += s.month_ret_sum
        if -0.05 <= s.dist_to_high <= 0.05:
            score += 0.5
            rationale.append("Proche du plus haut 52s")
        if -0.05 <= s.dist_to_low <= 0.05:
            score -= 0.5
            rationale.append("Proche du plus bas 52s")
        if s.news_sentiment > 0.05:
            score += min(s.news_sentiment, 0.5)
            rationale.append("Sentiment positif")
        elif s.news_sentiment < -0.05:
            score += s.news_sentiment
            rationale.append("Sentiment négatif")
        if s.earnings_surprise is not None:
            if s.earnings_surprise > 0:
                score += min(s.earnings_surprise, 0.2)
                rationale.append("Surprise de résultats positive")
            else:
                score += max(s.earnings_surprise, -0.2)
                rationale.append("Surprise de résultats négative")
        scored.append((s, score, "; ".join(rationale)))
    scored = sorted(scored, key=lambda x: x[1], reverse=True)
    return scored[:top_n]