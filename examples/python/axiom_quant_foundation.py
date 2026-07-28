"""
AXIOM QUANT FOUNDATIONAL EXAMPLES (MLX ACCELERATED)
====================================================
Running Stochastic Calculus, Black-Scholes Greeks, L2 Orderbook, and Portfolio Optimization.
"""

import time
import mlx.core as mx
from mlx.quant import (
    simulate_gbm,
    black_scholes_greeks,
    simulate_l2_orderbook,
    vpin_toxicity,
    markowitz_efficient_frontier,
)

def main():
    print("=" * 70)
    print("  AXIOM QUANT — FOUNDATION MODULE v1.0 (MLX ACCELERATED)")
    print("=" * 70)

    # 1. Stochastic Calculus: Geometric Brownian Motion
    print("\n[1] STOCHASTIC CALCULUS: Geometric Brownian Motion (GBM)")
    S0, mu, sigma, T, steps, num_paths = 100.0, 0.08, 0.20, 1.0, 252, 1000
    
    t0 = time.perf_counter()
    gbm_paths = simulate_gbm(S0, mu, sigma, T, steps, num_paths)
    mx.eval(gbm_paths)
    t1 = time.perf_counter()
    
    print(f"    Paths shape      : {gbm_paths.shape}")
    print(f"    S0               : {S0:.2f}")
    print(f"    Terminal Mean S  : {mx.mean(gbm_paths[:, -1]).item():.4f}")
    print(f"    Compute time     : {(t1 - t0) * 1000:.3f} ms")

    # 2. Options Analytics: Black-Scholes Greeks
    print("\n[2] OPTIONS ANALYTICS: Black-Scholes Greeks Engine")
    S, K, T_opt, r, vol = 100.0, 105.0, 0.5, 0.05, 0.20
    greeks = black_scholes_greeks(S, K, T_opt, r, vol, option_type="call")
    
    print(f"    Call Option Price: ${greeks['price'].item():.4f}")
    print(f"    Delta (Δ)        : {greeks['delta'].item():.4f}")
    print(f"    Gamma (Γ)        : {greeks['gamma'].item():.4f}")
    print(f"    Vega  (ν)        : {greeks['vega'].item():.4f}")
    print(f"    Theta (Θ)        : {greeks['theta'].item():.4f}")

    # 3. Market Microstructure: L2 Orderbook & VPIN
    print("\n[3] MARKET MICROSTRUCTURE: Level-2 Orderbook & VPIN Toxicity")
    ob = simulate_l2_orderbook(depth=5, mid_price=100.0)
    vpin = vpin_toxicity(ob["bid_volumes"], ob["ask_volumes"])
    mx.eval(ob["bids"], ob["asks"], vpin)
    
    print(f"    Top Bid / Ask    : {ob['bids'][0].item():.2f} / {ob['asks'][0].item():.2f}")
    print(f"    Spread           : {ob['spread'].item():.4f}")
    print(f"    VPIN Toxicity    : {vpin.item():.4f}")

    # 4. Portfolio Optimization: Markowitz Efficient Frontier
    print("\n[4] PORTFOLIO OPTIMIZATION: Markowitz Efficient Frontier")
    mean_returns = mx.array([0.12, 0.15, 0.09, 0.18])
    cov_matrix = mx.array([
        [0.040, 0.015, 0.005, 0.010],
        [0.015, 0.060, 0.010, 0.020],
        [0.005, 0.010, 0.020, 0.005],
        [0.010, 0.020, 0.005, 0.090]
    ])
    
    t0 = time.perf_counter()
    frontier = markowitz_efficient_frontier(mean_returns, cov_matrix, num_portfolios=5000)
    mx.eval(frontier["returns"], frontier["optimal_weights"])
    t1 = time.perf_counter()
    
    print(f"    Portfolios Tested: 5,000")
    print(f"    Max Sharpe Ratio : {frontier['max_sharpe'].item():.4f}")
    print(f"    Optimal Weights  : {frontier['optimal_weights'].tolist()}")
    print(f"    Compute time     : {(t1 - t0) * 1000:.3f} ms")
    print("\n" + "=" * 70)
    print("  AXIOM QUANT FOUNDATIONAL SUITE VERIFIED SUCCESSFULLY △")
    print("=" * 70)

if __name__ == "__main__":
    main()
