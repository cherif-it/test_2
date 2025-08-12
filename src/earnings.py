from __future__ import annotations

from typing import Dict, Optional

import requests
import yfinance as yf


def fetch_last_earnings_surprise_fmp(symbol: str, api_key: str) -> Optional[float]:
    url = f"https://financialmodelingprep.com/api/v3/earnings-surprises/{symbol}"
    params = {"apikey": api_key}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        # FMP returns list sorted by date desc
        item = data[0]
        eps_actual = item.get("actualEarningResult")
        eps_est = item.get("estimatedEarning")
        if eps_actual is None or eps_est is None:
            return None
        if eps_est == 0:
            return None
        surprise = (float(eps_actual) - float(eps_est)) / abs(float(eps_est))
        return float(surprise)
    except Exception:
        return None


def fetch_last_earnings_surprise_yf(symbol: str) -> Optional[float]:
    try:
        t = yf.Ticker(symbol)
        df = t.earnings_dates
        if df is None or df.empty:
            return None
        # Try to infer surprise from columns if present
        for col in ["EPS Surprise", "Surprise(%)", "Surprise"]:
            if col in df.columns and not df[col].dropna().empty:
                val = df[col].dropna().iloc[-1]
                try:
                    return float(val) / 100.0 if "%" in col else float(val)
                except Exception:
                    continue
        return None
    except Exception:
        return None


def get_last_earnings_surprise(symbol: str, fmp_api_key: Optional[str]) -> Optional[float]:
    if fmp_api_key:
        s = fetch_last_earnings_surprise_fmp(symbol, fmp_api_key)
        if s is not None:
            return s
    return fetch_last_earnings_surprise_yf(symbol)