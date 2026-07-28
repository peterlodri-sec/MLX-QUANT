# Concept Map: The Five Threshold Domains

All five research areas on axiomquant.org share the same mathematical structure:
a critical parameter controlling a phase transition in a complex system.

## Unified Structure

```
Domain            Parameter      Below Critical          At Critical        Above Critical
─────────────────────────────────────────────────────────────────────────────────────────
Graph (Erdős)     p = edge prob  Fragmented components    Giant component    Connected
Ternary (BitNet)  scale factor   Continuous weights      Round to ±1        {-1,0,+1}
Portfolio (Mark.) Lagrange λ     Asset at zero weight    Asset enters       Asset dominates
Options (B-S)     volatility σ   Deep OTM (N(d)<.5)     ATM (N(d)=.5)      Deep ITM (N(d)>.5)
Dyadic (Rényi)    β parameter    Information preserved  1 bit/iter loss    Chaotic
```

## Mathematical Isomorphism

Each system has:
1. A **state space** (graph edges, weight matrix, portfolio vector, option price, bit sequence)
2. A **critical parameter** (p, scale, λ, σ, β)
3. A **threshold condition** (p=1/n, |w/scale|=0.5, w_i crosses zero, N(d)=0.5, β=2)
4. A **phase transition** — sharp change in macroscopic behavior at the threshold
5. A **scaling law** — how the transition sharpens as system size → ∞

## Graph → Ternary Bridge

The strongest bridge: Erdős–Rényi G(n,p) → BitNet b1.58

- Graph edges are like weights: present/absent (binary) or {-1,0,+1} (ternary)
- The giant component threshold at p=1/n mirrors the quantization threshold at |w/scale|=0.5
- Both are sharp transitions: below threshold, the structure is fragmented/continuous; above, it's connected/discrete
- The β₁ cycle rank measures how many "extra" cycles exist — this is the graph analog of sparsity in ternary weights

## Dyadic → Ternary Bridge

The dyadic transformation T(x) = 2x mod 1 and ternary quantization share a bit-shift structure:
- Dyadic: each iteration reveals one bit of the binary expansion
- Ternary: each weight is encoded in 2 bits (codes 0,1,2 → values -1,0,+1)
- Both operate on packed binary representations
- The Rényi β-transformation generalizes the dyadic map to arbitrary β — this is analogous to generalizing from binary {0,1} to ternary {-1,0,+1}

## Portfolio → Options Bridge

Both are optimization problems with Lagrange multipliers controlling thresholds:
- Portfolio: maximize Sharpe → assets enter at critical λ
- Options: maximize expected payoff → exercise at critical S > K
- The efficient frontier and the option payoff diagram are both convex hulls
- Risk-neutral pricing is the Lagrange dual of the Markowitz problem

## Research Lineage

```
Erdős & Rényi (1959) — random graphs, sharp thresholds
    │
    ├─→ Markowitz (1952) — portfolio selection, efficient frontier
    ├─→ Black & Scholes (1973) — option pricing, risk-neutral measure
    ├─→ Rényi (1957) — β-transformation, symbolic dynamics
    │       │
    │       └─→ Dyadic transformation → BitNet b1.58 (Ma et al., 2024)
    │
    └─→ O'Hara (1995) — market microstructure theory
            │
            └─→ Almgren & Chriss (2000) — optimal execution
```

## Threshold Commonality

The threshold itself is always a **balance point**:
- Graph: p=1/n balances component growth vs. fragmentation
- Ternary: |w/scale|=0.5 balances quantization accuracy vs. compression
- Portfolio: λ* balances return vs. risk
- Options: N(d)=0.5 balances probability of exercise vs. non-exercise
- Dyadic: β=2 balances information preservation vs. chaos
