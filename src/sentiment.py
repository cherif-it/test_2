from __future__ import annotations

from typing import Dict, List

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def score_headlines(articles: List[Dict]) -> float:
    if not articles:
        return 0.0
    analyzer = SentimentIntensityAnalyzer()
    scores = []
    for a in articles:
        text = " ".join(
            [
                a.get("title") or "",
                a.get("description") or "",
            ]
        ).strip()
        if not text:
            continue
        s = analyzer.polarity_scores(text)
        scores.append(s["compound"])
    if not scores:
        return 0.0
    return float(sum(scores) / len(scores))


def score_by_symbol(news_by_symbol: Dict[str, List[Dict]]) -> Dict[str, float]:
    return {sym: score_headlines(arts) for sym, arts in news_by_symbol.items()}