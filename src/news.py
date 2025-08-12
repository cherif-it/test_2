from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Dict, List, Optional

import feedparser
import requests


logger = logging.getLogger(__name__)


def _clean_headline(text: str) -> str:
    return (text or "").replace("\n", " ").strip()


def fetch_news_newsapi(
    query: str,
    api_key: str,
    from_days: int = 7,
    language: str = "en",
    page_size: int = 50,
) -> List[Dict]:
    """Fetch news using NewsAPI (https://newsapi.org)."""
    url = "https://newsapi.org/v2/everything"
    from_date = (dt.datetime.utcnow() - dt.timedelta(days=from_days)).strftime("%Y-%m-%d")
    params = {
        "q": query,
        "from": from_date,
        "language": language,
        "sortBy": "relevancy",
        "pageSize": page_size,
        "apiKey": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("articles", [])
        return [
            {
                "title": _clean_headline(a.get("title", "")),
                "description": _clean_headline(a.get("description", "")),
                "source": a.get("source", {}).get("name"),
                "url": a.get("url"),
                "publishedAt": a.get("publishedAt"),
            }
            for a in articles
        ]
    except Exception as e:
        logger.warning("NewsAPI fetch error: %s", e)
        return []


def fetch_news_rss(feed_urls: List[str], limit_per_feed: int = 20) -> List[Dict]:
    results: List[Dict] = []
    for url in feed_urls:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:limit_per_feed]:
                results.append(
                    {
                        "title": _clean_headline(entry.get("title", "")),
                        "description": _clean_headline(entry.get("summary", "")),
                        "source": parsed.feed.get("title"),
                        "url": entry.get("link"),
                        "publishedAt": entry.get("published"),
                    }
                )
        except Exception as e:
            logger.warning("RSS fetch error for %s: %s", url, e)
    return results


DEFAULT_RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.investing.com/rss/news_25.rss",  # markets
    "https://www.investing.com/rss/news_301.rss",  # stocks
    "https://www.investing.com/rss/forex_1.rss",
]


def get_news_for_symbols(
    symbols: List[str],
    newsapi_key: Optional[str] = None,
    include_rss_fallback: bool = True,
) -> Dict[str, List[Dict]]:
    """Get news per symbol. If NewsAPI is available, query by symbol; else return general feed for all under key '__general__'."""
    results: Dict[str, List[Dict]] = {}
    if newsapi_key:
        for sym in symbols:
            arts = fetch_news_newsapi(query=sym, api_key=newsapi_key)
            if arts:
                results[sym] = arts
    if include_rss_fallback and not results:
        results["__general__"] = fetch_news_rss(DEFAULT_RSS_FEEDS)
    return results