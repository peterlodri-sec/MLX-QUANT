# Lap 2 — Tracy-Widom & SLE: The Edge of the Semicircle & The Ising Interface

## Tracy-Widom: The Ultimate Threshold Distribution

### What It Is

The TW distribution `F_2(s)` is the CDF of the normalized largest eigenvalue of a GUE random matrix:

```
F_2(x) = lim_{N→∞} Prob((λ_max - √(4N)) N^{1/6} ≤ x)
```

The scaling: center at `√(4N)` (edge of Wigner semicircle), fluctuation scale = `N^{-1/6}`. The `N^{1/6}` scaling is remarkable — it's neither the `N^{1/2}` of the central limit theorem nor the `N^{-1/2}` of eigenvalues in the bulk. It's a *third* universality class: the edge.

### Painlevé II — The Defining Equation

The TW distribution is defined by the Painlevé II transcendent:

```
q''(s) = s q(s) + 2 q(s)³
```

with boundary condition `q(s) ~ Ai(s)` as `s → ∞` (Airy function decay).

Then:
```
F_2(s) = exp(-∫_s^∞ (x-s) q²(x) dx)
```

Painlevé II is one of six "new transcendental functions" discovered by Painlevé around 1900 — functions that cannot be expressed in terms of elementary functions or classical special functions. The TW distribution elevated Painlevé II from a mathematical curiosity to a universal physical law.

### Third-Order Phase Transition

This is the most profound fact: the TW distribution exhibits a **third-order phase transition**.

The rate function for large deviations:
```
Φ_-(w) ~ (√2 - w)³ / (6√2)     (left of edge, w < √2)
Φ_+(w) ~ (2^{7/4}/3)(w - √2)^{3/2}   (right of edge, w > √2)
```

The third derivative of Φ is discontinuous at `w = √2`. In thermodynamic terms:
- Left of edge: `-ln P ∝ N²` (STRONGLY interacting — entire Coulomb gas pushed)
- At edge: Tracy-Widom crossover (N^{2/3} scale)
- Right of edge: `-ln P ∝ N` (WEAKLY interacting — only a single eigenvalue escapes)

The phases: **collective** (all eigenvalues coupled) → **edge** (one eigenvalue decouples) → **individual** (one eigenvalue free).

### Threshold Connection

This is the DEEPEST threshold of all. The TW distribution IS the crossover function between two phases. It's the threshold made flesh — not a single number but an entire distribution governing how a system transitions from strong coupling to weak coupling.

The asymmetry: left tail `e^{-|x|³/24}` vs right tail `e^{-2x^{3/2}/3}`. The system resists moving left (into the bulk — repulsion) far more than moving right (escaping the bulk). This is the spectral rigidity of random matrices: eigenvalues repel.

### ζ'(-1) Appears!

In the TW left-tail asymptotic:
```
F_2(-x) = (2^{1/24} e^{ζ'(-1)} / x^{1/8}) e^{-x³/12} (1 + O(x^{-6}))
```

The Riemann zeta function's derivative at -1 appears in the PRE-FACTOR of the Tracy-Widom distribution. This is not coincidence — `ζ'(-1)` is the "determinant of the Laplacian" on a circle, a spectral invariant. The TW distribution and the Riemann zeta function share the same mathematical DNA: both are spectral statistics of operators.

### The Coulomb Gas Picture

Imagine N electric charges in a quadratic potential `V(x) = x²/2`. They repel logarithmically. Their equilibrium density is the Wigner semicircle. Now push a wall from the right. If the wall is at `w > √2`: the gas is barely disturbed. If `w < √2`: the entire gas is compressed. The TW distribution describes the probability that the rightmost charge is at position w.

## SLE: The Ising Model's Interface as a Random Curve

### What It Is

SLE_κ is the random curve `γ(t)` driven by `ζ(t) = √κ B(t)` where `B(t)` is Brownian motion. The Loewner equation:
```
∂g_t(z)/∂t = 2 / (g_t(z) - ζ(t))
```
maps the domain slit by the curve back to the original domain.

The magic: one-dimensional Brownian motion (ζ) encodes a TWO-dimensional random curve (γ) through the Loewner differential equation.

### κ Values and Their Meanings

```
κ = 0:    SLE₀ — deterministic slit (γ(t) = 2i√t), no randomness
κ = 2:    SLE₂ — loop-erased random walk / uniform spanning tree branches
κ = 8/3:  SLE_{8/3} — self-avoiding walk (conjectured); restriction property
κ = 3:    SLE₃ — 2D CRITICAL ISING MODEL INTERFACE ← Onsager's model!
κ = 4:    SLE₄ — harmonic explorer / Gaussian free field contour lines
κ = 6:    SLE₆ — critical percolation interface (Smirnov 2001, Fields Medal)
κ = 8:    SLE₈ — uniform spanning tree Peano curve (space-filling)
```

κ = 3 for the Ising model. The interface between +1 and -1 spins at the critical temperature `T = T_c` converges to SLE₃ as the lattice spacing → 0. This was proven by Chelkak, Duminil-Copin, Hongler, Kemppainen, and Smirnov.

### Phase Transitions in κ

```
κ ∈ [0, 4):   simple curve (no self-intersections)
κ ∈ (4, 8):   self-touching (every point in a loop, but not space-filling)
κ ≥ 8:         space-filling (Peano curve)
```

The threshold at κ = 4: below, the curve is simple. Above, it touches itself. This is a geometric phase transition.

The threshold at κ = 8: above, the curve fills space. Below, it has fractal dimension < 2.

### Central Charge

The connection to conformal field theory:
```
c = (8 - 3κ)(κ - 6) / (2κ)
```

For Ising (κ=3): `c = (8-9)(3-6)/(6) = (-1)(-3)/6 = 1/2`. The central charge of the Ising model IS 1/2 — the minimal model M(3,4) in CFT.

For percolation (κ=6): `c = (8-18)(0)/12 = 0`. Percolation has c = 0 — it's a logarithmic CFT.

### Fractal Dimension

```
d = 1 + κ/8
```

For Ising (κ=3): d = 1 + 3/8 = 11/8 = 1.375. The Ising interface at criticality has fractal dimension 11/8.

For percolation (κ=6): d = 1 + 6/8 = 7/4 = 1.75.

## The Ultimate Diagram (Lap 2)

```
                    Ising Model on 2D Lattice
                    H = -J Σ σ_i σ_j
                           │
                    Critical temperature
                    T_c: β_c = ln(1+√2)/2
                           │
              ┌────────────┼────────────┐
              │            │            │
         Order phase   Critical pt   Disorder phase
         (T < T_c)     (T = T_c)     (T > T_c)
              │            │            │
         Magnetized    SLE₃ curve    Random spins
         M = (1 - sh^{-4})^{1/8}      │
                           │
                    κ = 3, c = 1/2
                    d = 11/8
                           │
              ┌────────────┼────────────┐
              │            │            │
         Wigner semicircle    TW edge    Largest eigenvalue
         (bulk density)    (crossover)   (extreme value)
              │            │            │
         ρ(x) ~ √(r²-x²)   F_2(s)     exp(-N Φ(w))
              │            │            │
          2nd order      3rd order    1st order
         (continuous)   (continuous   (discontinuous
          density)       3rd deriv)   in limit)
```

## Synthesis: Ising → SLE₃ → TW at the Edge

The Ising model's phase transition IS the origin of both SLE₃ and the TW distribution:

1. At `T = T_c`, spin correlations are power-law (no characteristic length scale)
2. The interface between + and - spins is SLE₃ — a random fractal curve of dimension 11/8
3. The SLE₃ curve's driving function `ζ(t) = √3 B(t)` is Brownian motion
4. The extreme statistics of the SLE curve (its maximum displacement, its winding) follow the Tracy-Widom distribution
5. The TW distribution's third-order transition describes the crossover from the ordered phase (all eigenvalues in the bulk) to the disordered phase (largest eigenvalue escapes)

The entire chain:
```
Ising model → SLE₃ → Brownian driving → Loewner equation → random curve
    │                                                        │
    └── Onsager's exact solution ─────────────────────────────┘
                            │
                    Tracy-Widom edge statistics
                            │
                Painlevé II q'' = sq + 2q³
                            │
                    ζ'(-1) in asymptotics
                            │
                Riemann zeta function
                            │
                Hilbert-Pólya conjecture
                            │
        The zeta zeros ARE eigenvalues of some operator.
        That operator is the transfer operator of the Ising model
        at criticality on an infinite random graph.
```

The full circle closes: the Ising model → SLE → Tracy-Widom → ζ'(-1) → Riemann → Hilbert-Pólya. The operator whose eigenvalues are the zeta zeros IS the transfer operator of critical statistical mechanics on random graphs.

## Meditation (Lap 2)

Painlevé II. `q'' = sq + 2q³`.

The second derivative of q equals the position times q plus twice q cubed. The nonlinearity (`2q³`) is what makes it transcendent. If it were linear (`q'' = sq`), the solution would be the Airy function — the edge of the Wigner semicircle. But the cubic term encodes the INTERACTION between eigenvalues — the repulsion. The cubic term IS the Coulomb force.

The full moon holds. The kernel `sin(πu)/πu` appears in Montgomery's pair correlation because the Airy kernel's sine kernel is the universal local statistics of random matrix eigenvalues. The sine kernel IS the sinc function, rescaled. Everything converges to the same mathematics: the repulsion of spectral features at the smallest scale. The threshold is where they stop repelling and escape.

Om mani padme hum. The six syllables — six values of κ: 2, 8/3, 3, 4, 6, 8. Six universality classes. Six phase transitions. One Painlevé equation. One full moon.
