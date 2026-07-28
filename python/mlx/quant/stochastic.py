import math
import mlx.core as mx

def simulate_gbm(S0: float, mu: float, sigma: float, T: float, steps: int, num_paths: int) -> mx.array:
    """
    Simulate Geometric Brownian Motion paths using MLX random normal generation.
    
    dS = mu * S * dt + sigma * S * dW
    """
    dt = T / steps
    # Generate random normal numbers: shape (num_paths, steps)
    dW = mx.random.normal(shape=(num_paths, steps)) * math.sqrt(dt)
    
    # Calculate drift component per step
    drift = (mu - 0.5 * sigma ** 2) * dt
    
    # Compute log increments
    log_returns = drift + sigma * dW
    
    # Cumulative sum over steps axis
    cum_returns = mx.cumsum(log_returns, axis=1)
    
    # Pad initial price S0 at time t=0
    zeros = mx.zeros((num_paths, 1))
    cum_returns_padded = mx.concatenate([zeros, cum_returns], axis=1)
    
    # S(t) = S0 * exp(cumsum)
    paths = S0 * mx.exp(cum_returns_padded)
    return paths


def _norm_cdf(x: mx.array) -> mx.array:
    """Standard normal cumulative distribution function via erf."""
    return 0.5 * (1.0 + mx.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: mx.array) -> mx.array:
    """Standard normal probability density function."""
    return (1.0 / math.sqrt(2.0 * math.pi)) * mx.exp(-0.5 * (x ** 2))


def black_scholes_greeks(S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"):
    """
    Calculate analytical Black-Scholes Option Price and Greeks (Delta, Gamma, Vega, Theta, Rho).
    Returns a dictionary of MLX scalar arrays.
    """
    S_arr = mx.array(S)
    K_arr = mx.array(K)
    T_arr = mx.array(T)
    r_arr = mx.array(r)
    sig_arr = mx.array(sigma)

    sqrt_T = mx.sqrt(T_arr)
    d1 = (mx.log(S_arr / K_arr) + (r_arr + 0.5 * sig_arr ** 2) * T_arr) / (sig_arr * sqrt_T)
    d2 = d1 - sig_arr * sqrt_T

    N_d1 = _norm_cdf(d1)
    N_d2 = _norm_cdf(d2)
    n_d1 = _norm_pdf(d1)

    disc = mx.exp(-r_arr * T_arr)

    if option_type.lower() == "call":
        price = S_arr * N_d1 - K_arr * disc * N_d2
        delta = N_d1
        theta = (- (S_arr * n_d1 * sig_arr) / (2.0 * sqrt_T) - r_arr * K_arr * disc * N_d2)
        rho = K_arr * T_arr * disc * N_d2
    else:
        N_minus_d1 = _norm_cdf(-d1)
        N_minus_d2 = _norm_cdf(-d2)
        price = K_arr * disc * N_minus_d2 - S_arr * N_minus_d1
        delta = N_d1 - 1.0
        theta = (- (S_arr * n_d1 * sig_arr) / (2.0 * sqrt_T) + r_arr * K_arr * disc * N_minus_d2)
        rho = -K_arr * T_arr * disc * N_minus_d2

    gamma = n_d1 / (S_arr * sig_arr * sqrt_T)
    vega = S_arr * n_d1 * sqrt_T

    return {
        "price": price,
        "delta": delta,
        "gamma": gamma,
        "vega": vega,
        "theta": theta,
        "rho": rho,
    }
