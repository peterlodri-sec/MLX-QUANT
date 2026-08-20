"""
Axiom Quant Foundation Module for MLX
======================================
Accelerated Quantitative Reasoning, Stochastic Calculus, Market Microstructure,
Portfolio Optimization, and BitNet b1.58 Ternary Quantization on Apple Silicon.
"""

from .armillary import ArmillarySphereLinear, armillary_sparse_update_metal
from .bitnet import (
    TernaryLinear,
    convert_model_to_bitnet,
    quantize_ternary_numpy,
    unpack_ternary_numpy,
    matmul_ternary_cpu_fallback,
)
from .microstructure import simulate_l2_orderbook, vpin_toxicity
from .portfolio import markowitz_efficient_frontier
from .stochastic import black_scholes_greeks, simulate_gbm

__all__ = [
    "ArmillarySphereLinear",
    "armillary_sparse_update_metal",
    "simulate_gbm",
    "black_scholes_greeks",
    "simulate_l2_orderbook",
    "vpin_toxicity",
    "markowitz_efficient_frontier",
    "TernaryLinear",
    "convert_model_to_bitnet",
    "quantize_ternary_numpy",
    "unpack_ternary_numpy",
    "matmul_ternary_cpu_fallback",
]

