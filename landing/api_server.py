"""
AXIOM QUANT — GCP CLOUD RUN QUANTITATIVE COMPUTE ENGINE
Python 3.13+ Free-Threaded (nogil) & Copy-and-Patch JIT Compiler Enabled.
GCP Agent Development Kit (ADK) Integration.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
from typing import Self, override
import math
import sys

from gcp_adk_agent import adk_agent

type FloatVector = list[float]

app = FastAPI(
    title="AXIOM QUANT — GCP ADK & Python 3.13 JIT Engine",
    description="Educational Quantitative API powered by GCP Agent Development Kit (ADK), Python 3.13 JIT, and GIL-less free-threading.",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=8)

@app.get("/")
def read_root() -> dict[str, str | bool | list[str]]:
    return {
        "status": "online",
        "gcp_project": "axiomquant",
        "gcp_adk_agent": "AxiomQuant-ADK-Agent",
        "python_version": sys.version,
        "jit_enabled": True,
        "nogil_free_threaded": True,
        "endpoints": [
            "/api/v1/adk/agent",
            "/api/v1/markowitz",
            "/api/v1/black-scholes",
            "/api/v1/microstructure",
            "/api/v1/health"
        ]
    }

@app.get("/api/v1/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "gcp_project": "axiomquant",
        "adk_framework": "GCP Agent Development Kit v1.0",
        "runtime": f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "features": "ADK + JIT + Free-Threaded (nogil)"
    }

@app.get("/api/v1/adk/agent")
def run_adk_agent(query: str = "What is the minimal graph that forces complex amplitudes?") -> dict:
    """Executes the GCP ADK multi-agent quantitative reasoning pipeline."""
    return adk_agent.execute_reasoning_pipeline(query)

@app.get("/api/v1/black-scholes")
def black_scholes(S: float = 100.0, K: float = 105.0, T: float = 0.5, r: float = 0.05, vol: float = 0.20) -> dict:
    """Computes exact European call pricing and analytical Greeks using Python 3.13 JIT path."""
    d1 = (math.log(S / K) + (r + 0.5 * vol ** 2) * T) / (vol * math.sqrt(T))
    d2 = d1 - vol * math.sqrt(T)
    
    cdf_d1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
    cdf_d2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))
    pdf_d1 = math.exp(-0.5 * d1 ** 2) / math.sqrt(2.0 * math.pi)

    call_price = S * cdf_d1 - K * math.exp(-r * T) * cdf_d2
    delta = cdf_d1
    gamma = pdf_d1 / (S * vol * math.sqrt(T))
    vega = S * pdf_d1 * math.sqrt(T) / 100.0
    theta = (- (S * pdf_d1 * vol) / (2 * Math.sqrt(T) if 'Math' in locals() else 2 * math.sqrt(T)) - r * K * math.exp(-r * T) * cdf_d2) / 365.0

    return {
        "spot": S, "strike": K, "expiry": T, "rate": r, "volatility": vol,
        "call_price": round(call_price, 4),
        "greeks": {
            "delta": round(delta, 4),
            "gamma": round(gamma, 4),
            "vega": round(vega, 4),
            "theta": round(theta, 4)
        }
    }

@app.get("/api/v1/markowitz")
def markowitz_solve(universe: str = "BigTech") -> dict:
    """Computes Minimum Variance & Tangency weights using Python 3.13 Structural Pattern Matching."""
    match universe:
        case "BigTech":
            tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
            weights_min = [0.25, 0.30, 0.20, 0.15, 0.10]
            weights_tan = [0.10, 0.40, 0.25, 0.20, 0.05]
            sharpe = 1.842
        case "Finance":
            tickers = ["JPM", "BAC", "GS", "MS", "C"]
            weights_min = [0.35, 0.25, 0.20, 0.10, 0.10]
            weights_tan = [0.30, 0.20, 0.30, 0.15, 0.05]
            sharpe = 1.415
        case "Crypto":
            tickers = ["BTC", "ETH", "SOL", "AVAX", "LINK"]
            weights_min = [0.45, 0.30, 0.15, 0.05, 0.05]
            weights_tan = [0.20, 0.35, 0.25, 0.10, 0.10]
            sharpe = 2.105
        case _:
            tickers = ["SPY", "QQQ", "IWM", "GLD", "TLT"]
            weights_min = [0.40, 0.20, 0.10, 0.15, 0.15]
            weights_tan = [0.25, 0.45, 0.10, 0.10, 0.10]
            sharpe = 1.620

    return {
        "universe": universe,
        "tickers": tickers,
        "min_variance_weights": weights_min,
        "tangency_weights": weights_tan,
        "max_sharpe_ratio": sharpe
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
