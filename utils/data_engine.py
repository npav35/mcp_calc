import asyncio
import logging
import time
import yfinance as yf
import pandas as pd
from datetime import datetime
from .data_types import CacheEntry, OptionDataRequest

'''Handles the caching (TTL) and yfinance data fetching'''

# Global Cache
option_cache = {}
CACHE_TTL = 60

async def fetch_live_option_data(req: OptionDataRequest) -> dict:
    ticker = req.ticker
    option_type = req.option_type
    expiration_date = req.expiration_date
    strike = req.strike
    
    stock = yf.Ticker(ticker)
    
    hist = await asyncio.to_thread(stock.history, period="1d")
    if hist.empty:
        raise ValueError(f"Could not fetch price for {ticker}")
    S = hist['Close'].iloc[-1]

    expirations = await asyncio.to_thread(lambda: stock.options)
    if not expirations:
        raise ValueError(f"No options found for {ticker}")
        
    if not expiration_date:
        expiration_date = expirations[0]
        
    opt = await asyncio.to_thread(stock.option_chain, expiration_date)
    chain = opt.calls if option_type.lower() == "call" else opt.puts
    
    if chain.empty:
        raise ValueError(f"No {option_type}s found for {ticker} on {expiration_date}")

    if strike is None:
        idx = (chain['strike'] - S).abs().idxmin()
    else:
        idx = (chain['strike'] - strike).abs().idxmin()
        
    selected_option = chain.loc[idx]
    K = selected_option['strike']
    sigma = selected_option['impliedVolatility']
    
    return {
        "S": S, "K": K, "T": (datetime.strptime(expiration_date, "%Y-%m-%d") - datetime.now()).days / 365.0,
        "r": 0.045, "sigma": sigma, "option_type": option_type
    }

async def get_available_expirations(ticker: str) -> list[str]:
    """Fetch all available expiration dates for a ticker."""
    stock = yf.Ticker(ticker)
    expirations = await asyncio.to_thread(lambda: stock.options)
    if not expirations:
        return []
    return sorted(list(expirations))

async def fetch_rsi(
    ticker: str,
    period: str = "6mo",
    interval: str = "1d",
    window: int = 14
) -> dict:
    """
    Fetch close prices from yfinance and compute RSI.
    Uses Wilder's smoothing (RMA) for a standard RSI implementation.
    """
    valid_periods = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}

    # Handle common LLM tool-call mistake: numeric period intended as RSI window.
    if isinstance(period, int) or (isinstance(period, str) and period.strip().isdigit()):
        window = int(period)
        period = "6mo"
    else:
        period = str(period).strip()
        if period not in valid_periods:
            logging.warning(
                "Invalid RSI period '%s' for %s. Falling back to '6mo'.",
                period,
                ticker,
            )
            period = "6mo"

    if isinstance(window, str):
        if not window.strip().isdigit():
            raise ValueError("window must be a positive integer")
        window = int(window)

    if window <= 0:
        raise ValueError("window must be a positive integer")

    ticker = ticker.strip().upper()
    stock = yf.Ticker(ticker)

    fetch_attempts = [
        lambda: stock.history(period=period, interval=interval),
        lambda: yf.download(
            tickers=ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        ),
        lambda: stock.history(period="1y", interval="1d"),
    ]

    hist = pd.DataFrame()
    last_error = None
    for attempt in fetch_attempts:
        for _ in range(2):
            try:
                hist = await asyncio.to_thread(attempt)
                if not hist.empty and "Close" in hist:
                    break
            except Exception as e:
                last_error = e
            await asyncio.sleep(0.25)
        if not hist.empty and "Close" in hist:
            break

    if hist.empty or "Close" not in hist:
        details = f" ({last_error})" if last_error else ""
        raise ValueError(f"Could not fetch price history for {ticker}{details}")

    close = hist["Close"].dropna()
    if len(close) < window + 1:
        raise ValueError(
            f"Not enough data to compute RSI for {ticker}. "
            f"Need at least {window + 1} close values."
        )

    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(100)

    latest_rsi = float(rsi.iloc[-1])
    latest_close = float(close.iloc[-1])
    latest_ts = close.index[-1]

    return {
        "ticker": ticker.upper(),
        "rsi": latest_rsi,
        "window": window,
        "period": period,
        "interval": interval,
        "latest_close": latest_close,
        "as_of": latest_ts.isoformat() if hasattr(latest_ts, "isoformat") else str(latest_ts),
        "signal": (
            "overbought" if latest_rsi >= 70
            else "oversold" if latest_rsi <= 30
            else "neutral"
        ),
    }
