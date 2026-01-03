# Options Greek Engine (MCP Server)

A high-performance Model Context Protocol (MCP) server for fetching option chains and calculating Black-Scholes Greeks. Designed with **low-latency determinism** and **resilient concurrency** at its core.

## Key Features & Architecture

This server is built to handle high-load scenarios while maintaining ultra-low response times:

*   **Modular Architecture**: Clean separation of concerns between math logic (`utils/greeks.py`), data fetching (`utils/data_engine.py`), and the service layer (`main.py`).
*   **Stale-While-Revalidate (SWR) Caching**: Eliminates the "jitter" of network I/O. Subsequent requests for the same instrument are served in **micro-seconds**, with background refreshes keeping data fresh without blocking the caller.
*   **Asynchronous Backpressure Pipeline**: Uses a bounded `asyncio.Queue` (depth: 5) to ensure the system remains stable and responsive even under extreme burst traffic.
*   **Load Shedding**: Implements a "Drop Newest" policy to protect deterministic performance for existing requests when at capacity.

### Architecture Diagram

```mermaid
graph TD
    subgraph Client_Layer ["Client Layer"]
        A["Finance_Model Agent"]
        B["Stress Test Utility"]
    end

    subgraph MCP_Server ["mcp_calc (Server)"]
        C["SSE/HTTP Transport"]
        D["Bounded Queue (Backpressure)"]
        
        subgraph Engine ["Core Engine"]
            E["SWR Cache"]
            F["Worker Pool"]
            G["Greeks Math (utils)"]
        end
    end

    A <--> C
    B <--> C
    C <--> D
    D <--> E
    E <--> F
    F <--> G
```

## Performance
*Benchmarks measured on local hardware.*

| Metric | Pre-Optimization | Post-Optimization (Cache Hit) | Improvement |
| :--- | :--- | :--- | :--- |
| `get_option_data` | **126 ms** | **46 µs** | **~2,700x** |
| Response Variance | High (Network) | **Ultra-Low (Deterministic)** | **Stable** |

## Available Tools

- `get_option_data`: Fetch S, K, T, r, and σ with intelligent defaults.
- `calculate_delta`: Calculate Option Delta (Δ).
- `calculate_gamma`: Calculate Option Gamma (Γ).
- `calculate_theta`: Calculate Option Theta (Θ).
- `calculate_vega`: Calculate Option Vega (ν).
- `calculate_rho`: Calculate Option Rho (ρ).

## Usage

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the server**:
   ```bash
   python main.py
   ```

For detailed metrics and methodology, see [benchmarks/BENCHMARKS.md](benchmarks/BENCHMARKS.md).

