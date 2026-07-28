# The Dyadic-Ternary Bridge

## How the doubling map becomes BitNet b1.58

### Dyadic Foundation

The dyadic transformation T(x) = 2x mod 1 operates on the unit interval [0,1).
In binary, x = 0.b₀b₁b₂..., and T(x) shifts left one bit: T(x) = 0.b₁b₂b₃...

Properties:
- 1 bit of information lost per iteration
- Rational inputs → periodic orbits (binary expansion repeats)
- Irrational inputs → chaotic orbits (never repeats)
- Invariant measure: Lebesgue (uniform) measure on [0,1)

### Rényi's β-Transformation

T_β(x) = βx mod 1, for β > 1.

- β = 2: standard dyadic (doubling) map
- β < 2: information preserved (contraction)
- β > 2: exponential chaos (expansion)
- β = golden ratio (φ ≈ 1.618): the "golden" β-transformation, used in A/D conversion
- β = 3/2: Parry's β-transformation, used in number theory

### Ternary Quantization as β-Transformation

BitNet b1.58 quantizes weights to {-1, 0, +1}. The quantization function:

```
code(w) = round(clamp(w/scale, -1, 1)) + 1     // {0, 1, 2} → {-1, 0, +1}
```

This is structurally identical to a 3-symbol β-transformation:
- Partition the real line into 3 intervals: (-∞, -scale/2), [-scale/2, scale/2], (scale/2, ∞)
- Map each interval to a symbol: -1, 0, +1
- The "doubling" becomes "tripling" — 2-symbol binary → 3-symbol ternary

### Information-Theoretic Bridge

| Concept             | Dyadic (Binary)      | Ternary (BitNet)     |
|--------------------|---------------------|---------------------|
| Symbols per step   | 2 ({0,1})           | 3 ({-1,0,+1})       |
| Bits per symbol    | 1                   | log₂(3) ≈ 1.58     |
| Compression ratio  | 2x (binary)         | 16x (fp32→2bit)    |
| Threshold          | β = 2               | |w/scale| = 0.5     |
| Critical behavior  | Chaos at β > 2      | Quantization at boundary |

### Why 1.58 Bits?

log₂(3) ≈ 1.58496... — this is the information content of a single ternary digit.
A ternary weight carries 1.58 bits of information, compared to 1 bit for binary.
This is why BitNet b1.58 matches FP16 performance: 1.58 bits per weight is the
exact information floor for language modeling at scale.

### From Dyadic to Graph

The dyadic map T(x) = 2x mod 1 is a deterministic dynamical system.
When we introduce randomness (noise in the bit stream), we get the Bernoulli process.
When we introduce structure (correlations between bits), we get a random graph.

The bridge chain is:
```
Dyadic Map → Bernoulli Process → Random Graph → Ternary Quantization
   (deterministic)    (stochastic)      (structural)      (compressive)
```

At each step, another dimension of information is introduced:
- Dyadic: pure deterministic chaos
- Bernoulli: independent random bits
- Graph: correlated random edges
- Ternary: quantized weights with graph structure

### Open Questions

1. What is the exact β for ternary quantization? It's not 2 — it's somewhere between
   β=2 (binary channel) and β=3 (ternary channel). The effective β depends on the
   sparsity pattern of the weight matrix.

2. Can we prove a "threshold theorem" for BitNet analogous to the Erdős–Rényi theorem?
   At what group_size does the quantized model cross from "unusable" to "matches FP16"?

3. The dyadic map's Frobenius–Perron operator has a clean spectrum. Does the ternary
   quantization operator have a similar spectral decomposition?

4. β₁ (cycle rank) measures graph complexity. Does there exist a "quantization rank"
   that measures how far a ternary matrix is from being real-realizable?
