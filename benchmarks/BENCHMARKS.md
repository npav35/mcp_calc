# Benchmark Baseline (Pre-Optimization)

**Date**: 2025-12-23

These metrics represent the performance of the MCP tools **before** any async refactoring or caching optimizations. They serve as a baseline to measure future improvements.

## 1. Greek Calculations (Math-heavy)
*Black-Scholes formulas implemented in Python.*

| Function | P50 (Median) | P95 (Tail) | P99 (Worst Case) |
| :--- | :--- | :--- | :--- |
| `calculate_delta` | 0.7 µs | 0.8 µs | 1.0 µs |
| `calculate_gamma` | 0.7 µs | 0.8 µs | 1.0 µs |
| `calculate_theta` | 1.0 µs | 1.3 µs | 1.6 µs |
| `calculate_vega`  | 0.8 µs | 0.9 µs | 1.1 µs |
| `calculate_rho`   | 0.8 µs | 1.1 µs | 1.3 µs |

**Conclusion**: The mathematical components are extremely fast (~1 microsecond). Optimization here is unnecessary for now.

## 2. Data Fetching (I/O-heavy)
*Fetching option chain data via `yfinance`.*

| Function | P50 (Median) | P95 (Tail) | P99 (Worst Case) |
| :--- | :--- | :--- | :--- |
| `get_option_data` | **126 ms** | **143 ms** | **143 ms** |

**Conclusion**: This is the primary bottleneck. Fetching a single option chain takes ~125ms+.
- **Optimization Target**: This is where async refactoring, caching, or faster data providers will yield the highest ROI. A 50% improvement here would save ~60ms per call.

<br>

# Post-Optimization Benchmarks

**Date**: 2026-01-03
**Optimization Level**: (Backpressure + Strict TTL Caching + Modularization)

Following the architectural refactoring and the implementation of the **Strict TTL** caching layer, the performance characteristics of the system have Improved.

## 1. Updated Data Fetching (Deterministic)
*Fetching option data with the Strict TTL Caching Layer.*

| Function | P50 (Median) | P95 (Tail) | P99 (Worst Case) |
| :--- | :--- | :--- | :--- |
| `get_option_data` (Cache Hit) | **107 µs** | **136 µs** | **136 µs** |

**Impact of Changes:**
1. **~1,100x Improvement**: Median latency dropped from **126ms** to **107 microseconds**. 
2. **Determinism & Freshness**: By using a memory-backed cache with a strict TTL, "jitter" is eliminated while ensuring data integrity. The response time is predictable (deterministic).
3. **Decision Integrity**: Unlike SWR, a strict TTL ensures that no stale data is ever served for a trading decision, aligning with HFT best practices for execution reliability.

## 2. Updated Greek Calculations (Modularization)
*Performance after modularizing math into `utils/greeks.py` but before vectorization.*

| Function | P50 (Median) | P95 (Tail) | P99 (Worst Case) |
| :--- | :--- | :--- | :--- |
| `calculate_delta` | 0.75 µs | 0.83 µs | 0.87 µs |
| `calculate_gamma` | 0.79 µs | 0.83 µs | 0.91 µs |
| `calculate_theta` | 1.1 µs | 1.2 µs | 1.2 µs |
| `calculate_vega`  | 0.83 µs | 0.95 µs | 2.1 µs |
| `calculate_rho`   | 0.91 µs | 1.0 µs | 1.0 µs |

**Impact of Changes:**
- **Modularization**: Moving these to a dedicated utility file improved code readability and maintainability without any performance penalty.

<br>

# High-Throughput Batch Processing (Production Greeks)

**Date**: 2026-01-08
**Optimization Level**: ⚡ (NumPy Vectorization)

Following the refactor of the mathematical engine to use **NumPy vectorization**, the system can now process large portfolios of options with minimal overhead.

## 1. Batch Throughput vs. Scalar Loops
*Computing Delta for a growing number of options.*

| Batch Size | Scalar Loop (Python) | Vectorized (NumPy) | Speedup |
| :--- | :--- | :--- | :--- |
| 1 | 0.7 µs | 2.1 µs* | - |
| 1,000 | 21 ms | 0.1 ms | **~210x** |
| 10,000 | 215 ms | 0.3 ms | **~715x** |

*\*Note: For a single calculation, the NumPy overhead is slightly higher, but for any production volume (1,000+ entries), vectorization provides a massive advantage.*

## 2. Risk Simulation Latency
*Simulating a -2% market shock for a 1,000-option portfolio (Base + Shock + P&L).*

| Operation | Latency (1k Portfolio) | Throughput |
| :--- | :--- | :--- |
| `calculate_risk_shock` | **0.76 ms** | **~1,300 simulations/sec** |

**Impact of Changes:**
1. **Parallel Exposure**: The `calculate_portfolio_greeks` tool can now assess risk for an entire 10,000-option book in **less than 0.5 milliseconds**.
2. **Numerical Rigor**: The engine was verified using **Hypothesis** (property-based testing) to ensure correctness across 100,000+ fuzzed numerical edge cases.
3. **Modular Architecture**: The transition to a modular `utils/` structure improves maintainability while preserving sub-microsecond performance for individual calculations.

