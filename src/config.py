import os
from dataclasses import dataclass
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    newsapi_key: str | None
    fmp_api_key: str | None
    default_period: str
    default_interval: str
    universes: Dict[str, List[str]]


def get_config() -> AppConfig:
    newsapi_key = os.getenv("NEWSAPI_KEY")
    fmp_api_key = os.getenv("FMP_API_KEY")

    universes = {
        # Actions US (exemples)
        "equities": [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "JNJ",
            "XOM", "WMT", "PG", "MA", "HD", "UNH", "AMD", "NFLX", "KO", "PFE",
        ],
        # ETFs (exemples)
        "etf": [
            "SPY", "QQQ", "IWM", "EEM", "GLD", "SLV", "TLT", "HYG", "XLF", "XLK",
        ],
        # Cryptos via Yahoo Finance (suffixe -USD)
        "crypto": [
            "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD",
        ],
        # Indices (tickers Yahoo)
        "indices": [
            "^GSPC", "^NDX", "^DJI", "^RUT", "^VIX", "^STOXX50E",
        ],
        # Matières premières (exemples via Yahoo)
        "commodities": [
            "GC=F", "SI=F", "CL=F", "NG=F", "ZC=F", "ZW=F",
        ],
        # Forex (paires Yahoo)
        "forex": [
            "EURUSD=X", "USDJPY=X", "GBPUSD=X", "USDCAD=X", "AUDUSD=X", "USDCHF=X",
        ],
        # Obligations via ETFs comme proxy (exemples)
        "bonds": [
            "TLT", "IEF", "BND", "HYG", "LQD",
        ],
    }

    return AppConfig(
        newsapi_key=newsapi_key,
        fmp_api_key=fmp_api_key,
        default_period="1y",
        default_interval="1d",
        universes=universes,
    )