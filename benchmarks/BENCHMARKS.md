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
**Optimization Level**: (Backpressure + SWR Caching + Modularization)

Following the architectural refactoring and the implementation of the **Stale-While-Revalidate (SWR)** caching layer, the performance characteristics of the system have Improved.

## 1. Updated Data Fetching (Deterministic)
*Fetching option data with the Stale-While-Revalidate Caching Layer.*

| Function | P50 (Median) | P95 (Tail) | P99 (Worst Case) |
| :--- | :--- | :--- | :--- |
| `get_option_data` (Cache Hit) | **46 µs** | **58 µs** | **58 µs** |

**Impact of Changes:**
1. **~2,700x Improvement**: Median latency dropped from **126ms** to **46 microseconds**. 
2. **Determinism**: By using a memory-backed cache, "jitter" caused by network calls to Yahoo Finance has been eliminated. The response time is now extremely predictable (deterministic).
3. **Concurrency Resilience**: The implementation of the **Bounded Queue (Backpressure)** ensures that even during a cache miss or a high-load burst, the server protects itself from resource exhaustion, prioritizing stability over processing outdated requests.

## 2. Updated Greek Calculations
*Performance remains consistent after modularization into `utils/greeks.py`.*

| Function | P50 (Median) | P95 (Tail) | P99 (Worst Case) |
| :--- | :--- | :--- | :--- |
| `calculate_delta` | 0.75 µs | 0.83 µs | 0.87 µs |
| `calculate_gamma` | 0.79 µs | 0.83 µs | 0.91 µs |
| `calculate_theta` | 1.1 µs | 1.2 µs | 1.2 µs |
| `calculate_vega`  | 0.83 µs | 0.95 µs | 2.1 µs |
| `calculate_rho`   | 0.91 µs | 1.0 µs | 1.0 µs |

**Impact of Changes:**
- **Modularization**: Moving these to a dedicated utility file improved code readability and maintainability without any performance penalty. In fact, cache hits for data mean the Greeks loop can execute thousands of times per second.

