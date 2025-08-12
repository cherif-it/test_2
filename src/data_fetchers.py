from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import io
import re

import pandas as pd
import requests
import yfinance as yf


def chunked(items: List[str], size: int) -> List[List[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _is_valid_price_df(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        return False
    cols = {c.lower() for c in df.columns}
    return "close" in cols and not df["Close"].dropna().empty


def _normalize_to_us_ticker(symbol: str) -> str | None:
    # Stooq expects symbols like aapl.us, msft.us, etc.
    if re.fullmatch(r"[A-Za-z]{1,5}", symbol):
        return symbol.lower() + ".us"
    return None


def _fetch_single_stooq_csv(symbol: str, period: str, interval: str) -> pd.DataFrame | None:
    try:
        stq_sym = _normalize_to_us_ticker(symbol)
        if not stq_sym:
            return None
        # interval mapping: daily d, weekly w, monthly m
        i = "d"
        if interval == "1wk":
            i = "w"
        elif interval == "1mo":
            i = "m"
        url = f"https://stooq.com/q/d/l/?s={stq_sym}&i={i}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        if not resp.text or resp.text.strip().lower().startswith("<!doctype"):
            return None
        df = pd.read_csv(io.StringIO(resp.text))
        # Expect columns: Date,Open,High,Low,Close,Volume
        if "Date" not in df.columns or "Close" not in df.columns:
            return None
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"]).set_index("Date").sort_index()
        # Trim by period roughly
        if period in ("6mo", "1y", "2y", "5y"):
            months = {"6mo": 6, "1y": 12, "2y": 24, "5y": 60}[period]
            cutoff = df.index.max() - pd.DateOffset(months=months)
            df = df[df.index >= cutoff]
        # Ensure standard columns case
        for c in ["Open", "High", "Low", "Close", "Volume"]:
            if c not in df.columns:
                return None
        return df if _is_valid_price_df(df) else None
    except Exception:
        return None


def download_market_data(
    tickers: Iterable[str], period: str = "1y", interval: str = "1d"
) -> Dict[str, pd.DataFrame]:
    ticker_list = list(dict.fromkeys([t.strip() for t in tickers if t and t.strip()]))
    if not ticker_list:
        return {}

    data_by_ticker: Dict[str, pd.DataFrame] = {}

    for batch in chunked(ticker_list, 20):
        df = None
        try:
            df = yf.download(
                tickers=batch,
                period=period,
                interval=interval,
                group_by="ticker",
                auto_adjust=False,
                threads=True,
                progress=False,
            )
        except Exception:
            df = None

        if df is not None and isinstance(df.columns, pd.MultiIndex):
            for t in batch:
                ok = False
                try:
                    if t in df.columns.get_level_values(0):
                        sub = df[t].copy()
                        sub.columns.name = None
                        sub = sub.dropna(how="all")
                        if _is_valid_price_df(sub):
                            data_by_ticker[t] = sub
                            ok = True
                except Exception:
                    ok = False
                if not ok:
                    stq = _fetch_single_stooq_csv(t, period, interval)
                    if _is_valid_price_df(stq):
                        data_by_ticker[t] = stq
        elif df is not None and not isinstance(df.columns, pd.MultiIndex):
            t = batch[0]
            ok = False
            try:
                df = df.dropna(how="all")
                if _is_valid_price_df(df):
                    data_by_ticker[t] = df
                    ok = True
            except Exception:
                ok = False
            if not ok:
                stq = _fetch_single_stooq_csv(t, period, interval)
                if _is_valid_price_df(stq):
                    data_by_ticker[t] = stq
        else:
            for t in batch:
                stq = _fetch_single_stooq_csv(t, period, interval)
                if _is_valid_price_df(stq):
                    data_by_ticker[t] = stq

    return data_by_ticker


def compute_daily_returns(price_df: pd.DataFrame) -> pd.Series:
    close = price_df["Close"].astype(float)
    return close.pct_change().dropna()


def compute_rolling_extremes(
    price_df: pd.DataFrame, window_days: int = 252
) -> Tuple[pd.Series, pd.Series]:
    close = price_df["Close"].astype(float)
    roll_max = close.rolling(window_days, min_periods=20).max()
    roll_min = close.rolling(window_days, min_periods=20).min()
    return roll_max, roll_min


def summarize_ticker(price_df: pd.DataFrame) -> Dict[str, float]:
    if price_df is None or price_df.empty or "Close" not in price_df.columns or price_df["Close"].dropna().empty:
        raise ValueError("No price data available")
    close = price_df["Close"].astype(float).dropna()
    last = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) >= 2 else last
    day_chg = (last - prev) / prev if prev else 0.0

    high_52w, low_52w = compute_rolling_extremes(price_df)
    last_high = float(high_52w.dropna().iloc[-1]) if not high_52w.dropna().empty else last
    last_low = float(low_52w.dropna().iloc[-1]) if not low_52w.dropna().empty else last

    distance_to_high = (last - last_high) / last_high if last_high else 0.0
    distance_to_low = (last - last_low) / last_low if last_low else 0.0

    monthly_ret = float(close.pct_change().rolling(21).sum().iloc[-1]) if len(close) >= 21 else 0.0

    return {
        "last": last,
        "day_chg": day_chg,
        "last_52w_high": last_high,
        "last_52w_low": last_low,
        "dist_to_high": distance_to_high,
        "dist_to_low": distance_to_low,
        "month_ret_sum": monthly_ret,
    }