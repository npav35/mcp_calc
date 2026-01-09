import numpy as np
import time
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.analytics import perform_risk_shock

def benchmark_risk_shock(size=1000):
    S = [100.0] * size
    K = [100.0] * size
    T = [0.5] * size
    r = [0.05] * size
    sigma = [0.2] * size
    types = ["call"] * size
    positions = [1.0] * size
    shock = -0.02
    
    # Warmup
    perform_risk_shock(S, K, T, r, sigma, types, positions, shock)
    
    start = time.perf_counter()
    perform_risk_shock(S, K, T, r, sigma, types, positions, shock)
    elapsed = time.perf_counter() - start
    
    print(f"Risk Shock (Portfolio Size {size}): {elapsed*1000:.4f}ms")

if __name__ == "__main__":
    benchmark_risk_shock(1000)
