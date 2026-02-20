import sys
import os
import asyncio
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data_engine import fetch_ema


class _FakeTicker:
    def __init__(self, history_df):
        self._history_df = history_df

    def history(self, period="6mo", interval="1d"):
        return self._history_df


def test_fetch_ema_happy_path(monkeypatch):
    idx = pd.date_range("2025-01-01", periods=30, freq="D")
    close = pd.Series(range(100, 130), index=idx)
    hist = pd.DataFrame({"Close": close})

    monkeypatch.setattr("utils.data_engine.yf.Ticker", lambda ticker: _FakeTicker(hist))
    monkeypatch.setattr("utils.data_engine.yf.download", lambda **kwargs: pd.DataFrame())

    result = asyncio.run(fetch_ema("aapl", window=20))

    expected = float(close.ewm(span=20, adjust=False, min_periods=20).mean().iloc[-1])

    assert result["ticker"] == "AAPL"
    assert result["window"] == 20
    assert result["ema"] == pytest.approx(expected)
    assert result["latest_close"] == pytest.approx(float(close.iloc[-1]))
    assert result["signal"] == "price_above_ema"


def test_fetch_ema_rejects_non_positive_window(monkeypatch):
    idx = pd.date_range("2025-01-01", periods=5, freq="D")
    hist = pd.DataFrame({"Close": pd.Series(range(100, 105), index=idx)})

    monkeypatch.setattr("utils.data_engine.yf.Ticker", lambda ticker: _FakeTicker(hist))
    monkeypatch.setattr("utils.data_engine.yf.download", lambda **kwargs: pd.DataFrame())

    with pytest.raises(ValueError, match="window must be a positive integer"):
        asyncio.run(fetch_ema("MSFT", window=0))
