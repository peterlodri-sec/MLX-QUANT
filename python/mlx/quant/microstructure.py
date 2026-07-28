import mlx.core as mx


def simulate_l2_orderbook(
    depth: int = 10, mid_price: float = 100.0, tick_size: float = 0.01
):
    """
    Simulate a Level-2 Limit Order Book (Bids & Asks depth).
    Returns dict containing bid_prices, bid_volumes, ask_prices, ask_volumes.
    """
    half_depth = depth

    # Generate prices
    bid_offsets = mx.arange(1, half_depth + 1, dtype=mx.float32) * tick_size
    ask_offsets = mx.arange(1, half_depth + 1, dtype=mx.float32) * tick_size

    bids = mid_price - bid_offsets
    asks = mid_price + ask_offsets

    # Random volumes exponentially decaying with depth
    raw_bid_vols = mx.random.uniform(low=100.0, high=1000.0, shape=(half_depth,))
    raw_ask_vols = mx.random.uniform(low=100.0, high=1000.0, shape=(half_depth,))

    decay = mx.exp(-0.15 * mx.arange(half_depth, dtype=mx.float32))

    bid_volumes = raw_bid_vols * decay
    ask_volumes = raw_ask_vols * decay

    return {
        "bids": bids,
        "bid_volumes": bid_volumes,
        "asks": asks,
        "ask_volumes": ask_volumes,
        "mid_price": mx.array(mid_price),
        "spread": asks[0] - bids[0],
    }


def vpin_toxicity(buy_volumes: mx.array, sell_volumes: mx.array) -> mx.array:
    """
    Compute Volume-Synchronized Probability of Toxicity (VPIN).
    VPIN = sum(|V_buy - V_sell|) / sum(V_total)
    """
    imbalance = mx.abs(buy_volumes - sell_volumes)
    total_volume = mx.sum(buy_volumes + sell_volumes)

    vpin = mx.sum(imbalance) / (total_volume + 1e-8)
    return vpin
