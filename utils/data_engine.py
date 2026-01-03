import asyncio
import logging
import time
import yfinance as yf
from datetime import datetime
from .data_types import CacheEntry, OptionDataRequest

'''Handles the caching (SWR) and yfinance data fetching'''

# Global Cache
option_cache = {}
CACHE_TTL = 60
CACHE_SWR = 300

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

async def refresh_cache_entry(key, original_req: OptionDataRequest):
    ticker, option_type, expiration_date, strike = key
    try:
        refresh_req = OptionDataRequest(
            ticker=ticker,
            option_type=option_type,
            expiration_date=expiration_date,
            strike=strike,
            future=asyncio.get_running_loop().create_future()
        )
        data = await fetch_live_option_data(refresh_req)
        option_cache[key] = CacheEntry(data=data, timestamp=time.time())
        logging.info(f"CACHE REFRESHED: {ticker}")
    except Exception as e:
        logging.error(f"CACHE REFRESH FAILED: {ticker} - {e}")
    finally:
        if key in option_cache:
            option_cache[key].is_refreshing = False
