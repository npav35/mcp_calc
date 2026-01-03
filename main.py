import asyncio
import logging
import time
from fastmcp import FastMCP

# Utils
from utils.metrics import time_execution
from utils.greeks import (
    calculate_delta as bs_delta, 
    calculate_gamma as bs_gamma, 
    calculate_theta as bs_theta, 
    calculate_vega as bs_vega, 
    calculate_rho as bs_rho
)
from utils.data_types import OptionDataRequest, CacheEntry
from utils.data_engine import (
    option_cache, 
    fetch_live_option_data, 
    refresh_cache_entry, 
    CACHE_TTL, 
    CACHE_SWR
)

mcp = FastMCP("My Server")

# --- Pipeline Definitions ---

# Global Queue (Bounded for Backpressure)
request_queue = asyncio.Queue(maxsize=5) 

async def process_option_request(req: OptionDataRequest):
    """
    Worker function to process a single option data request.
    Orchestrates caching and live fetching via utils.
    """
    ticker = req.ticker
    option_type = req.option_type
    expiration_date = req.expiration_date
    strike = req.strike
    
    # Generate Cache Key
    cache_key = (ticker, option_type, expiration_date, strike)
    now = time.time()
    
    # 1. Check Cache
    if cache_key in option_cache:
        entry = option_cache[cache_key]
        age = now - entry.timestamp
        
        if age < CACHE_TTL:
            logging.info(f"CACHE HIT (FRESH): {ticker}")
            if not req.future.done():
                req.future.set_result(entry.data)
            return

        if age < CACHE_SWR:
            logging.info(f"CACHE HIT (STALE): {ticker}. Triggering background refresh.")
            if not req.future.done():
                req.future.set_result(entry.data)
            
            if not entry.is_refreshing:
                entry.is_refreshing = True
                asyncio.create_task(refresh_cache_entry(cache_key, req))
            return
            
    # 2. Cache Miss / Too Old
    logging.info(f"CACHE MISS: {ticker}")
    try:
        result = await fetch_live_option_data(req)
        if not req.future.done():
            req.future.set_result(result)
        option_cache[cache_key] = CacheEntry(data=result, timestamp=time.time())
    except Exception as e:
        if not req.future.done():
            req.future.set_exception(e)

async def worker():
    """Background worker loop"""
    logging.info("Worker started.")
    while True:
        req = await request_queue.get()
        try:
            await process_option_request(req)
        except Exception as e:
            logging.error(f"Worker error: {e}")
        finally:
            request_queue.task_done()

worker_task = None

def ensure_worker_running():
    global worker_task
    if worker_task is None or worker_task.done():
        worker_task = asyncio.create_task(worker())

# --- MCP Tool Registrations ---

@mcp.tool()
@time_execution
async def get_option_data(ticker: str, option_type: str, expiration_date: str = None, strike: float = None) -> dict:
    """Fetch option data using backpressure pipeline."""
    ensure_worker_running()
    if request_queue.full():
        raise RuntimeError("System Overloaded: Request queue is full.")

    fut = asyncio.get_running_loop().create_future()
    req = OptionDataRequest(ticker, option_type, expiration_date, strike, fut)
    
    try:
        request_queue.put_nowait(req)
    except asyncio.QueueFull:
         raise RuntimeError("System Overloaded: Request queue is full.")
    
    return await fut

@mcp.tool()
@time_execution
def calculate_delta(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """Calculate the delta of an option."""
    return bs_delta(S, K, T, r, sigma, option_type)

@mcp.tool()
@time_execution
def calculate_gamma(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """Calculate the gamma of an option."""
    return bs_gamma(S, K, T, r, sigma, option_type)

@mcp.tool()
@time_execution
def calculate_theta(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """Calculate the theta of an option."""
    return bs_theta(S, K, T, r, sigma, option_type)

@mcp.tool()
@time_execution
def calculate_vega(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """Calculate the vega of an option."""
    return bs_vega(S, K, T, r, sigma, option_type)

@mcp.tool()
@time_execution
def calculate_rho(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """Calculate the rho of an option."""
    return bs_rho(S, K, T, r, sigma, option_type)

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=3000)
