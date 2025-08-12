from __future__ import annotations

import os
from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import get_config
from data_fetchers import download_market_data
from news import get_news_for_symbols
from sentiment import score_by_symbol
from analytics import build_summaries, top_gainers_losers, top_52w_highs_lows, investment_suggestions

st.set_page_config(page_title="Marchés & Idées", layout="wide")

cfg = get_config()


@st.cache_data(show_spinner=False)
def load_data(asset_class: str, period: str, interval: str) -> Dict[str, pd.DataFrame]:
    symbols = cfg.universes.get(asset_class, [])
    return download_market_data(symbols, period=period, interval=interval)


@st.cache_data(show_spinner=False)
def load_news_and_sentiment(symbols: List[str]) -> Dict[str, float]:
    news = get_news_for_symbols(symbols, newsapi_key=cfg.newsapi_key)
    return score_by_symbol(news)


def render_price_chart(df: pd.DataFrame, title: str):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="OHLC",
            )
        ]
    )
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10), title=title)
    st.plotly_chart(fig, use_container_width=True)


# Sidebar
st.sidebar.title("Configuration")
asset_class = st.sidebar.selectbox(
    "Classe d'actifs",
    options=list(cfg.universes.keys()),
    index=list(cfg.universes.keys()).index("equities"),
)
period = st.sidebar.selectbox("Période", ["6mo", "1y", "2y", "5y"], index=1)
interval = st.sidebar.selectbox("Intervalle", ["1d", "1wk", "1mo"], index=0)

st.title("Dashboard Marchés et Idées d'Investissement")

with st.spinner("Chargement des données..."):
    data = load_data(asset_class, period, interval)

symbols = list(data.keys())

with st.spinner("Analyse de sentiment actualités..."):
    sentiment_by_symbol = load_news_and_sentiment(symbols)

summaries = build_summaries(data, news_sentiment_by_symbol=sentiment_by_symbol, fmp_api_key=cfg.fmp_api_key)

# Top sections
top_n = st.sidebar.slider("Top N", min_value=5, max_value=20, value=10, step=1)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Top Gagnants / Perdants (Journée)")
    gainers, losers = top_gainers_losers(summaries, top_n=top_n)
    st.write(
        pd.DataFrame(
            [
                {
                    "Symbole": s.symbol,
                    "Dernier": round(s.last, 4),
                    "% Jour": round(s.day_chg * 100.0, 2),
                }
                for s in gainers
            ]
        )
    )
    st.write(
        pd.DataFrame(
            [
                {
                    "Symbole": s.symbol,
                    "Dernier": round(s.last, 4),
                    "% Jour": round(s.day_chg * 100.0, 2),
                }
                for s in losers
            ]
        )
    )

with col2:
    st.subheader("Plus hauts / bas 52 semaines")
    highs, lows = top_52w_highs_lows(summaries, top_n=top_n)
    st.write(
        pd.DataFrame(
            [
                {
                    "Symbole": s.symbol,
                    "% vs Haut 52s": round(s.dist_to_high * 100.0, 2),
                    "Dernier": round(s.last, 4),
                }
                for s in highs
            ]
        )
    )
    st.write(
        pd.DataFrame(
            [
                {
                    "Symbole": s.symbol,
                    "% vs Bas 52s": round(s.dist_to_low * 100.0, 2),
                    "Dernier": round(s.last, 4),
                }
                for s in lows
            ]
        )
    )

with col3:
    st.subheader("Idées d'investissement (règles)")
    ideas = investment_suggestions(summaries, top_n=top_n)
    st.write(
        pd.DataFrame(
            [
                {
                    "Symbole": s.symbol,
                    "Score": round(score, 3),
                    "Raisons": rationale,
                    "Sentiment": round(s.news_sentiment, 3),
                    "Surprise": None if s.earnings_surprise is None else round(s.earnings_surprise, 3),
                }
                for (s, score, rationale) in ideas
            ]
        )
    )

# Detail view
st.subheader("Détails et Graphiques")
sel = st.multiselect("Sélectionner des symboles", options=symbols, default=symbols[: min(5, len(symbols))])

for sym in sel:
    df = data[sym]
    render_price_chart(df, title=sym)