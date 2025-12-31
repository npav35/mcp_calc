import asyncio
import math
import yfinance as yf
from datetime import datetime
from fastmcp import FastMCP
from utils.metrics import time_execution

mcp = FastMCP("My Server")


@mcp.tool()
@time_execution
async def get_option_data(ticker: str, option_type: str, expiration_date: str = None, strike: float = None) -> dict:
    """
    Fetch option data for a given ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        option_type: "call" or "put"
        expiration_date: Expiration date in "YYYY-MM-DD" format. Defaults to the nearest expiration.
        strike: Strike price. Defaults to the strike closest to the current price.
        
    Returns:
        Dictionary containing S, K, T, r, sigma, and option_type.
    """
    stock = yf.Ticker(ticker)
    
    # Get current price (blocking)
    try:
        hist = await asyncio.to_thread(stock.history, period="1d")
        S = hist['Close'].iloc[-1]
    except IndexError:
        raise ValueError(f"Could not fetch price for {ticker}")

    # Get expiration dates (blocking property access)
    expirations = await asyncio.to_thread(lambda: stock.options)
    if not expirations:
        raise ValueError(f"No options found for {ticker}")
        
    if not expiration_date:
        expiration_date = expirations[0]
    elif expiration_date not in expirations:
        raise ValueError(f"Expiration {expiration_date} not found. Available: {expirations}")

    # Calculate time to expiration (T)
    expiry = datetime.strptime(expiration_date, "%Y-%m-%d")
    today = datetime.now()
    T = (expiry - today).days / 365.0
    if T <= 0:
        T = 0.001 # Avoid division by zero or negative time

    # Get option chain (blocking)
    opt = await asyncio.to_thread(stock.option_chain, expiration_date)
    chain = opt.calls if option_type.lower() == "call" else opt.puts
    
    if chain.empty:
        raise ValueError(f"No {option_type}s found for {ticker} on {expiration_date}")

    # Find strike
    if strike is None:
        # Find strike closest to current price
        idx = (chain['strike'] - S).abs().idxmin()
        selected_option = chain.loc[idx]
    else:
        # Find strike closest to requested strike
        idx = (chain['strike'] - strike).abs().idxmin()
        selected_option = chain.loc[idx]
        
    K = selected_option['strike']
    sigma = selected_option['impliedVolatility']
    
    # Risk-free rate (using a placeholder or fetching 13-week treasury bill could be an enhancement, 
    # but for now we'll use a standard 4.5% or let the user override if we added that param, 
    # but the tool signature doesn't have it. Let's return a default.)
    r = 0.045 

    return {
        "S": S,
        "K": K,
        "T": T,
        "r": r,
        "sigma": sigma,
        "option_type": option_type
    }

@mcp.tool()
@time_execution
def calculate_delta(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """
    Calculate the delta of an option using the Black-Scholes model.
    
    Args:
        S: Current price of the underlying asset
        K: Strike price of the option
        T: Time to expiration in years
        r: Risk-free interest rate (decimal, e.g., 0.05 for 5%)
        sigma: Volatility of the underlying asset (decimal, e.g., 0.2 for 20%)
        option_type: "call" or "put"
    """
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    
    # CDF of standard normal distribution
    cdf_d1 = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
    
    if option_type.lower() == "call":
        return cdf_d1
    elif option_type.lower() == "put":
        return cdf_d1 - 1
    else:
        raise ValueError("option_type must be 'call' or 'put'")

@mcp.tool()
@time_execution
def calculate_gamma(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """
    Calculate the gamma of an option using the Black-Scholes model.
    
    Args:
        S: Current price of the underlying asset
        K: Strike price of the option
        T: Time to expiration in years
        r: Risk-free interest rate (decimal, e.g., 0.05 for 5%)
        sigma: Volatility of the underlying asset (decimal, e.g., 0.2 for 20%)
        option_type: "call" or "put"
    """
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    
    # Gamma is the second derivative of the option price with respect to the underlying price
    gamma = math.exp(-0.5 * d1 ** 2) / (math.sqrt(2 * math.pi) * S * sigma * math.sqrt(T))
    
    return gamma

@mcp.tool()
@time_execution
def calculate_theta(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """
    Calculate the theta of an option using the Black-Scholes model.
    
    Args:
        S: Current price of the underlying asset
        K: Strike price of the option
        T: Time to expiration in years
        r: Risk-free interest rate (decimal, e.g., 0.05 for 5%)
        sigma: Volatility of the underlying asset (decimal, e.g., 0.2 for 20%)
        option_type: "call" or "put"
    """
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    # PDF of standard normal distribution
    pdf_d1 = (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2)
    
    # CDF of standard normal distribution for d2
    cdf_d2 = 0.5 * (1 + math.erf(d2 / math.sqrt(2)))
    cdf_neg_d2 = 0.5 * (1 + math.erf(-d2 / math.sqrt(2)))
    
    term1 = -(S * sigma * pdf_d1) / (2 * math.sqrt(T))
    
    if option_type.lower() == "call":
        theta = term1 - r * K * math.exp(-r * T) * cdf_d2
    elif option_type.lower() == "put":
        theta = term1 + r * K * math.exp(-r * T) * cdf_neg_d2
    else:
        raise ValueError("option_type must be 'call' or 'put'")
        
    return theta

@mcp.tool()
@time_execution
def calculate_vega(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """
    Calculate the vega of an option using the Black-Scholes model.
    
    Args:
        S: Current price of the underlying asset
        K: Strike price of the option
        T: Time to expiration in years
        r: Risk-free interest rate (decimal, e.g., 0.05 for 5%)
        sigma: Volatility of the underlying asset (decimal, e.g., 0.2 for 20%)
        option_type: "call" or "put" (Vega is the same for both, but parameter kept for consistency)
    """
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    
    # PDF of standard normal distribution
    pdf_d1 = (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2)
    
    # Vega calculation: S * sqrt(T) * N'(d1)
    # This represents the rate of change of the option value with respect to the volatility of the underlying asset.
    # Note: This returns Vega for a 100% change in volatility (e.g. 0.20 to 1.20). 
    # To get Vega for a 1% change, divide by 100.
    vega = S * math.sqrt(T) * pdf_d1
    
    # Basic validation for option_type even though it doesn't affect calculation
    if option_type.lower() not in ["call", "put"]:
         raise ValueError("option_type must be 'call' or 'put'")

    return vega

@mcp.tool()
@time_execution
def calculate_rho(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """
    Calculate the rho of an option using the Black-Scholes model.
    
    Args:
        S: Current price of the underlying asset
        K: Strike price of the option
        T: Time to expiration in years
        r: Risk-free interest rate (decimal, e.g., 0.05 for 5%)
        sigma: Volatility of the underlying asset (decimal, e.g., 0.2 for 20%)
        option_type: "call" or "put"
    """
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    # CDF of standard normal distribution for d2
    cdf_d2 = 0.5 * (1 + math.erf(d2 / math.sqrt(2)))
    cdf_neg_d2 = 0.5 * (1 + math.erf(-d2 / math.sqrt(2)))
    
    # Rho calculation:
    # Call: K * T * e^(-r*T) * N(d2)
    # Put: -K * T * e^(-r*T) * N(-d2)
    # This returns Rho for a 100% change in interest rate (e.g. 0.05 to 1.05).
    # To get Rho for a 1% change, divide by 100.
    
    if option_type.lower() == "call":
        rho = K * T * math.exp(-r * T) * cdf_d2
    elif option_type.lower() == "put":
        rho = -K * T * math.exp(-r * T) * cdf_neg_d2
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    return rho

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=3000)
