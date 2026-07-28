import mlx.core as mx

def markowitz_efficient_frontier(mean_returns: mx.array, cov_matrix: mx.array, num_portfolios: int = 1000):
    """
    Monte Carlo Markowitz Efficient Frontier Solver using MLX.
    
    mean_returns: (N,) array of expected asset returns
    cov_matrix: (N, N) asset covariance matrix
    num_portfolios: Number of random portfolio weight vectors to sample
    """
    n_assets = mean_returns.shape[0]
    
    # Sample random weights: shape (num_portfolios, n_assets)
    raw_weights = mx.random.uniform(low=0.0, high=1.0, shape=(num_portfolios, n_assets))
    weight_sums = mx.sum(raw_weights, axis=1, keepdims=True)
    weights = raw_weights / weight_sums
    
    # Portfolio Expected Return: E[R_p] = w @ mu
    portfolio_returns = mx.matmul(weights, mean_returns)
    
    # Portfolio Variance: Var(R_p) = diag(w @ cov @ w^T)
    # W_cov = weights @ cov_matrix -> shape (num_portfolios, n_assets)
    w_cov = mx.matmul(weights, cov_matrix)
    portfolio_vars = mx.sum(w_cov * weights, axis=1)
    portfolio_risks = mx.sqrt(portfolio_vars)
    
    # Sharpe Ratios (assuming risk-free rate = 0.02)
    risk_free_rate = 0.02
    sharpe_ratios = (portfolio_returns - risk_free_rate) / (portfolio_risks + 1e-8)
    
    # Index of Max Sharpe Ratio
    max_sharpe_idx = mx.argmax(sharpe_ratios)
    
    return {
        "returns": portfolio_returns,
        "risks": portfolio_risks,
        "sharpe_ratios": sharpe_ratios,
        "optimal_weights": weights[max_sharpe_idx],
        "max_sharpe": sharpe_ratios[max_sharpe_idx],
    }
