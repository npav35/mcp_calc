import numpy as np
from scipy.stats import norm

'''Handles the greek calculations with NumPy vectorization for high-throughput performance.'''

def _d1_d2(S, K, T, r, sigma):
    """
    Internal helper to calculate d1 and d2. Handles both scalar and array inputs.
    Includes safeguards against division by zero and extreme values.
    """
    # Safeguard T and sigma against zero to avoid division by zero
    T = np.maximum(T, 1e-9)
    sigma = np.maximum(sigma, 1e-9)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return d1, d2

def calculate_delta(S, K, T, r, sigma, option_type):
    """Vectorized calculation of Delta."""
    d1, _ = _d1_d2(S, K, T, r, sigma)
    
    if option_type == "call":
        return norm.cdf(d1)
    elif option_type == "put":
        return norm.cdf(d1) - 1
    else:
        # Vectorized string comparison
        is_call = np.array([ot.lower() == "call" for ot in np.atleast_1d(option_type)])
        res = norm.cdf(d1)
        # If output is an array, we can use where. 
        # If input was scalar, we handle it simply.
        if np.isscalar(option_type):
            return res if option_type.lower() == "call" else res - 1
        return np.where(is_call, res, res - 1)

def calculate_gamma(S, K, T, r, sigma, option_type=None):
    """Vectorized calculation of Gamma (Same for calls and puts)."""
    d1, _ = _d1_d2(S, K, T, r, sigma)
    # Ensure sigma and T are handled safely (already done in _d1_d2 for intermediate, 
    # but Gamma uses them in the denominator directly)
    T = np.maximum(T, 1e-9)
    sigma = np.maximum(sigma, 1e-9)
    
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    return gamma

def calculate_theta(S, K, T, r, sigma, option_type):
    """Vectorized calculation of Theta."""
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    T = np.maximum(T, 1e-9)
    
    term1 = -(S * sigma * norm.pdf(d1)) / (2 * np.sqrt(T))
    
    if np.isscalar(option_type):
        ot = option_type.lower()
        if ot == "call":
            return term1 - r * K * np.exp(-r * T) * norm.cdf(d2)
        else:
            return term1 + r * K * np.exp(-r * T) * norm.cdf(-d2)
            
    is_call = np.array([ot.lower() == "call" for ot in np.atleast_1d(option_type)])
    res_call = term1 - r * K * np.exp(-r * T) * norm.cdf(d2)
    res_put = term1 + r * K * np.exp(-r * T) * norm.cdf(-d2)
    return np.where(is_call, res_call, res_put)

def calculate_vega(S, K, T, r, sigma, option_type=None):
    """Vectorized calculation of Vega (Same for calls and puts)."""
    d1, _ = _d1_d2(S, K, T, r, sigma)
    T = np.maximum(T, 1e-9)
    
    vega = S * np.sqrt(T) * norm.pdf(d1)
    return vega

def calculate_rho(S, K, T, r, sigma, option_type):
    """Vectorized calculation of Rho."""
    _, d2 = _d1_d2(S, K, T, r, sigma)
    T = np.maximum(T, 1e-9)
    
    if np.isscalar(option_type):
        ot = option_type.lower()
        if ot == "call":
            return K * T * np.exp(-r * T) * norm.cdf(d2)
        else:
            return -K * T * np.exp(-r * T) * norm.cdf(-d2)

    is_call = np.array([ot.lower() == "call" for ot in np.atleast_1d(option_type)])
    res_call = K * T * np.exp(-r * T) * norm.cdf(d2)
    res_put = -K * T * np.exp(-r * T) * norm.cdf(-d2)
    return np.where(is_call, res_call, res_put)
