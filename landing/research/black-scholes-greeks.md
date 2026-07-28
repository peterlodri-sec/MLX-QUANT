# Black-Scholes Greeks — Reference Sheet

## The Black-Scholes PDE

```
∂V/∂t + ½σ²S²∂²V/∂S² + rS∂V/∂S - rV = 0
```

## The Black-Scholes Formula (European Call)

```
C = N(d₊)S - N(d₋)Ke^(-rτ)
P = N(-d₋)Ke^(-rτ) - N(-d₊)S    (put-call parity)

d₊ = [ln(S/K) + (r + σ²/2)τ] / (σ√τ)
d₋ = d₊ - σ√τ
```

## First-Order Greeks (Delta, Theta, Vega, Rho)

### Delta (Δ) — sensitivity to underlying price

```
Δ_call = N(d₊)                    ∈ [0, 1]
Δ_put  = N(d₊) - 1               ∈ [-1, 0]
```

Interpretation: for a $1 move in the underlying, the option price moves by $Δ.
Delta also approximates the risk-neutral probability of expiring ITM (for calls).

Threshold connection: Δ crosses 0.5 exactly at the point where the option
transitions from OTM to ITM in risk-neutral space. This is the same sharp
transition as the Erdős–Rényi giant component at p=1/n.

### Gamma (Γ) — rate of change of Delta (second derivative)

```
Γ = N'(d₊) / (Sσ√τ)              ≥ 0 (for both calls and puts)
N'(x) = (1/√(2π))e^(-x²/2)      (standard normal PDF)
```

Interpretation: how fast Delta changes as the underlying moves. Highest near ATM.
Gamma risk is why delta-hedging requires continuous rebalancing.

### Theta (Θ) — time decay

```
Θ_call = -[SN'(d₊)σ/(2√τ)] - rKe^(-rτ)N(d₋)
Θ_put  = -[SN'(d₊)σ/(2√τ)] + rKe^(-rτ)N(-d₋)
```

Interpretation: how much value the option loses per day as expiry approaches.
Theta is always negative for long option positions (time decay works against you).

### Vega (ν) — sensitivity to volatility (NOT a Greek letter!)

```
ν = S√τ · N'(d₊)                 ≥ 0 (for both calls and puts)
```

Interpretation: for a 1% change in implied volatility, the option price changes by ν/100.
Vega is highest for ATM options with medium time to expiry.

Threshold connection: σ is the one unobservable parameter. The volatility smile
shows that σ implied by market prices varies with strike — proving the model
assumption of constant σ is false. The smile *itself* encodes market beliefs
about tail risk.

### Rho (ρ) — sensitivity to risk-free rate

```
ρ_call = Kτe^(-rτ)N(d₋)          ≥ 0
ρ_put  = -Kτe^(-rτ)N(-d₋)        ≤ 0
```

Interpretation: for a 1% change in interest rates, the option price changes by ρ/100.
Rho is least important for short-dated options, most important for long-dated (LEAPS).

## Second-Order Greeks

### Vanna — ∂Δ/∂σ = ∂ν/∂S

```
Vanna = -N'(d₊) · d₋ / σ
```

### Charm — ∂Δ/∂τ = ∂Θ/∂S (delta decay)

```
Charm_call = -N'(d₊) · [2rτ - d₋σ√τ] / (2τσ√τ)
```

### Volga (Vomma) — ∂ν/∂σ (second-order vega)

```
Volga = ν · d₊d₋ / σ
```

## Numerical Example

```
S = 100, K = 100, τ = 1 year, σ = 20%, r = 5%

d₊ = [ln(1) + (0.05 + 0.04/2)·1] / (0.2·1) = 0.07 / 0.2 = 0.35
d₋ = 0.35 - 0.2 = 0.15

N(d₊) = N(0.35) ≈ 0.6368
N(d₋) = N(0.15) ≈ 0.5596

C = 0.6368·100 - 0.5596·100·e^(-0.05) = 63.68 - 53.23 = 10.45
P = 10.45 - 100 + 95.12 = 5.57   (put-call parity)
```

## The Volatility Smile (Threshold Artifact)

In a perfect Black-Scholes world, implied volatility is flat across strikes.
In reality, σ(K) forms a smile/smirk:

- OTM puts: σ(K) higher than ATM (crash risk premium)
- ATM: σ(K) at minimum
- OTM calls: σ(K) slightly higher (rally participation)

The smile IS the market's threshold map: at what σ does each strike become
fairly priced? The curvature encodes tail risk — the same way the efficient
frontier's curvature encodes correlation structure.
