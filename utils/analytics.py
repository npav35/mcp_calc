import numpy as np
from .greeks import calculate_delta, calculate_gamma

def perform_risk_shock(S, K, T, r, sigma, option_types, positions, shock_percent):
    """Core logic for risk shock simulation."""
    # Convert to NumPy arrays
    S_arr = np.array(S)
    K_arr = np.array(K)
    T_arr = np.array(T)
    r_arr = np.array(r)
    sigma_arr = np.array(sigma)
    pos_arr = np.array(positions)
    
    # 1. Base Metrics
    base_delta = calculate_delta(S_arr, K_arr, T_arr, r_arr, sigma_arr, option_types)
    base_gamma = calculate_gamma(S_arr, K_arr, T_arr, r_arr, sigma_arr, option_types)
    
    # 2. Shocked Metrics
    S_shocked = S_arr * (1.0 + shock_percent)
    shock_delta = calculate_delta(S_shocked, K_arr, T_arr, r_arr, sigma_arr, option_types)
    
    # 3. Dollar Greeks & P&L Estimates
    dollar_delta = np.sum(base_delta * pos_arr * S_arr * 100)
    
    # Delta P&L = Delta * dS
    # Gamma P&L = 0.5 * Gamma * dS^2
    dS = S_arr * shock_percent
    pnl_delta = np.sum(base_delta * pos_arr * dS * 100)
    pnl_gamma = np.sum(0.5 * base_gamma * pos_arr * (dS**2) * 100)
    
    return {
        "shock_percent": f"{shock_percent * 100:.2f}%",
        "portfolio_summary": {
            "total_dollar_delta": float(dollar_delta),
            "estimated_pnl_impact": float(pnl_delta + pnl_gamma),
            "delta_pnl_contribution": float(pnl_delta),
            "gamma_pnl_contribution": float(pnl_gamma)
        },
        "greeks_drift": {
            "base_net_delta": float(np.sum(base_delta * pos_arr)),
            "shocked_net_delta": float(np.sum(shock_delta * pos_arr))
        }
    }
