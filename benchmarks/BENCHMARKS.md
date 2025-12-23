# Benchmark Baseline (Pre-Optimization)

**Date**: 2025-12-23
**Device**: Mac (Local Execution)

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
