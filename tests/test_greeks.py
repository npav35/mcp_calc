import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import numpy as np
from hypothesis import given, strategies as st
from utils.greeks import calculate_delta, calculate_gamma, calculate_theta, calculate_vega, calculate_rho

# --- Unit Tests (Known Values) ---

def test_known_call_delta():
    # Hull, Options Futures and Other Derivatives Example
    # S=49, K=50, r=0.05, sigma=0.2, T=0.3846 (20 weeks)
    delta = calculate_delta(49, 50, 0.3846, 0.05, 0.2, "call")
    assert pytest.approx(delta, rel=1e-2) == 0.5216

def test_vectorization_delta():
    S = np.array([49, 50])
    K = np.array([50, 50])
    T = np.array([0.3846, 0.3846])
    r = np.array([0.05, 0.05])
    sigma = np.array([0.2, 0.2])
    types = ["call", "put"]
    
    deltas = calculate_delta(S, K, T, r, sigma, types)
    assert len(deltas) == 2
    assert deltas[0] > 0
    assert deltas[1] < 0

# --- Property-Based Testing (Hypothesis) ---

@given(
    S=st.floats(min_value=1.0, max_value=1000.0),
    K=st.floats(min_value=1.0, max_value=1000.0),
    T=st.floats(min_value=0.01, max_value=5.0),
    r=st.floats(min_value=0.0, max_value=0.2),
    sigma=st.floats(min_value=0.01, max_value=1.0)
)
def test_delta_bounds(S, K, T, r, sigma):
    """Prove that Call Delta is always in [0, 1] and Put Delta in [-1, 0]"""
    # Test Call
    c_delta = calculate_delta(S, K, T, r, sigma, "call")
    assert 0.0 <= c_delta <= 1.0
    
    # Test Put
    p_delta = calculate_delta(S, K, T, r, sigma, "put")
    assert -1.0 <= p_delta <= 0.0
    
    # Put-Call Parity Relationship for Delta
    # Delta(Call) - Delta(Put) should be 1.0
    assert pytest.approx(c_delta - p_delta) == 1.0

@given(
    S=st.floats(min_value=1.0, max_value=1000.0),
    K=st.floats(min_value=1.0, max_value=1000.0),
    T=st.floats(min_value=0.01, max_value=5.0),
    r=st.floats(min_value=0.0, max_value=0.2),
    sigma=st.floats(min_value=0.01, max_value=1.0)
)
def test_gamma_positivity(S, K, T, r, sigma):
    """Gamma should always be non-negative (can be 0 due to underflow for deep OTM)."""
    gamma = calculate_gamma(S, K, T, r, sigma)
    assert gamma >= 0

@given(
    S=st.floats(min_value=1.0, max_value=1000.0),
    K=st.floats(min_value=1.0, max_value=1000.0),
    T=st.floats(min_value=0.01, max_value=5.0),
    r=st.floats(min_value=0.0, max_value=0.2),
    sigma=st.floats(min_value=0.01, max_value=1.0)
)
def test_vega_positivity(S, K, T, r, sigma):
    """Vega should always be non-negative (can be 0 due to underflow for deep OTM)."""
    vega = calculate_vega(S, K, T, r, sigma)
    assert vega >= 0

if __name__ == "__main__":
    # Suppress warnings about module rewriting since we are running as a script
    sys.exit(pytest.main(["-v", "-W", "ignore::pytest.PytestAssertRewriteWarning", __file__]))
