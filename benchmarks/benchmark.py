import logging
import asyncio
import time
import sys
import os

# Add parent directory to path to import main
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import calculate_delta, calculate_gamma, calculate_theta, calculate_vega, calculate_rho, get_option_data

# Suppress metrics logging during benchmark
logging.getLogger("metrics").setLevel(logging.WARNING)

def benchmark_function(func, runs=1000, *args):
    """
    Run a function multiple times and return statistics.
    """
    times = []
    
    # If it's a FastMCP tool, access the underlying function
    callable_func = getattr(func, 'fn', func)
    
    # Warmup
    for _ in range(10):
        callable_func(*args)
        
    for _ in range(runs):
        start = time.perf_counter()
        if asyncio.iscoroutinefunction(callable_func):
            asyncio.run(callable_func(*args))
        else:
            callable_func(*args)
        end = time.perf_counter()
        times.append(end - start)
        
    sorted_times = sorted(times)
    count = len(sorted_times)
    
    return {
        "p50": sorted_times[int(count * 0.50)],
        "p95": sorted_times[int(count * 0.95)],
        "p99": sorted_times[int(count * 0.99)],
        "min": sorted_times[0],
        "max": sorted_times[-1]
    }

def print_stats(name, stats):
    print(f"\nBenchmark for: {name}")
    print(f"  P50: {stats['p50']:.9f} s")
    print(f"  P95: {stats['p95']:.9f} s")
    print(f"  P99: {stats['p99']:.9f} s")

if __name__ == "__main__":
    print("Running Benchmarks...")
    
    # Test parameters (ATM Call)
    S = 100.0  # Stock price
    K = 100.0  # Strike price
    T = 1.0    # Time to expiration (1 year)
    r = 0.05   # Risk-free rate
    sigma = 0.2 # Volatility
    option_type = "call"
    
    # Benchmark Greeks
    iterations = 10000
    
    stats_delta = benchmark_function(calculate_delta, iterations, S, K, T, r, sigma, option_type)
    print_stats("calculate_delta", stats_delta)
    
    stats_gamma = benchmark_function(calculate_gamma, iterations, S, K, T, r, sigma, option_type)
    print_stats("calculate_gamma", stats_gamma)
    
    stats_theta = benchmark_function(calculate_theta, iterations, S, K, T, r, sigma, option_type)
    print_stats("calculate_theta", stats_theta)

    stats_vega = benchmark_function(calculate_vega, iterations, S, K, T, r, sigma, option_type)
    print_stats("calculate_vega", stats_vega)

    stats_rho = benchmark_function(calculate_rho, iterations, S, K, T, r, sigma, option_type)
    print_stats("calculate_rho", stats_rho)

    # Benchmark Data Fetching (fewer iterations due to network latency)
    print("\nBenchmarking get_option_data (this may take a moment)...")
    try:
        # ticker="AAPL", option_type="call"
        stats_data = benchmark_function(get_option_data, 5, "AAPL", "call") 
        print_stats("get_option_data", stats_data)
    except Exception as e:
        print(f"Skipping get_option_data benchmark due to error: {e}")
    
    print("\nBenchmarking complete.")
