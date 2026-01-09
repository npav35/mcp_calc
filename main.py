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
from utils.analytics import perform_risk_shock
from utils.data_types import OptionDataRequest, CacheEntry
from utils.data_engine import (
    option_cache, 
    fetch_live_option_data, 
    CACHE_TTL
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
def calculate_portfolio_greeks(
    S: list[float], 
    K: list[float], 
    T: list[float], 
    r: list[float], 
    sigma: list[float], 
    option_types: list[str]
) -> dict:
    """
    High-speed batch calculation of Greeks for a portfolio of options.
    Uses NumPy vectorization for maximum throughput.
    """
    import numpy as np
    
    # Convert inputs to arrays
    S_arr = np.array(S)
    K_arr = np.array(K)
    T_arr = np.array(T)
    r_arr = np.array(r)
    sigma_arr = np.array(sigma)
    
    deltas = bs_delta(S_arr, K_arr, T_arr, r_arr, sigma_arr, option_types)
    gammas = bs_gamma(S_arr, K_arr, T_arr, r_arr, sigma_arr, option_types)
    thetas = bs_theta(S_arr, K_arr, T_arr, r_arr, sigma_arr, option_types)
    vegas = bs_vega(S_arr, K_arr, T_arr, r_arr, sigma_arr, option_types)
    rhos = bs_rho(S_arr, K_arr, T_arr, r_arr, sigma_arr, option_types)
    
    return {
        "deltas": deltas.tolist(),
        "gammas": gammas.tolist(),
        "thetas": thetas.tolist(),
        "vegas": vegas.tolist(),
        "rhos": rhos.tolist(),
        "total_delta": float(np.sum(deltas)),
        "total_gamma": float(np.sum(gammas))
    }

@mcp.tool()
@time_execution
def calculate_risk_shock(
    S: list[float], 
    K: list[float], 
    T: list[float], 
    r: list[float], 
    sigma: list[float], 
    option_types: list[str],
    positions: list[float],
    shock_percent: float
) -> dict:
    """
    Stress-test a portfolio by simulating a market shock.
    Includes Dollar Greeks and estimated P&L impact.
    """
    return perform_risk_shock(S, K, T, r, sigma, option_types, positions, shock_percent)

@mcp.tool()
@time_execution
def calculate_delta(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """Calculate the delta of an option."""
    return float(bs_delta(S, K, T, r, sigma, option_type))

@mcp.tool()
@time_execution
def calculate_gamma(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """Calculate the gamma of an option."""
    return float(bs_gamma(S, K, T, r, sigma, option_type))

@mcp.tool()
@time_execution
def calculate_theta(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """Calculate the theta of an option."""
    return float(bs_theta(S, K, T, r, sigma, option_type))

@mcp.tool()
@time_execution
def calculate_vega(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """Calculate the vega of an option."""
    return float(bs_vega(S, K, T, r, sigma, option_type))

@mcp.tool()
@time_execution
def calculate_rho(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """Calculate the rho of an option."""
    return float(bs_rho(S, K, T, r, sigma, option_type))

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=3000)
