"""
Axiom Quant Foundation Module for MLX
======================================
Accelerated Quantitative Reasoning, Stochastic Calculus, Market Microstructure,
and Portfolio Optimization on Apple Silicon.
"""

from .stochastic import simulate_gbm, black_scholes_greeks
from .microstructure import simulate_l2_orderbook, vpin_toxicity
from .portfolio import markowitz_efficient_frontier

__all__ = [
    "simulate_gbm",
    "black_scholes_greeks",
    "simulate_l2_orderbook",
    "vpin_toxicity",
    "markowitz_efficient_frontier",
]
