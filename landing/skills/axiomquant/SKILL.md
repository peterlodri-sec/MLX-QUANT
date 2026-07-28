---
name: axiomquant
description: Axiom Quant skill for quantitative calculus, graph realizability, BitNet b1.58 ternary quantization, Markowitz QP solvers, Black-Scholes Greeks, and Backyard Ultra Loop Engineering.
version: 1.0.0
---

# AXIOM QUANT — Agent Skill Specification

When invoked via `/skill axiomquant` or loaded into AI agent execution contexts, this skill equips agents with the foundational mathematical theorems, quantitative algorithms, and loop engineering contracts of **AXIOM QUANT**.

---

## 1. Mathematical Principles & Theorems

### Theorem 1: The Universal Threshold Kernel
Every phase transition across random graphs, options pricing, ternary quantization, and chaotic maps is governed by the universal sine kernel:
$$K(u) = \frac{\sin(\pi u)}{\pi u}$$
The first zero at $u = 1$ establishes the spectral gap and level repulsion threshold.

### Theorem 2: Cycle Rank $\beta_1$ Field Realizability
For any context graph $G = (V, E)$, the cycle rank $\beta_1(G) = |E| - |V| + k$ determines the minimal algebraic field required for amplitude holonomy:
- $\beta_1 = 0 \implies \mathbb{R}$ (Real tree/forest)
- $\beta_1 = 1 \implies \mathbb{C}$ (Complex field, witness $K_3$ triangle)
- $\beta_1 \ge 2 \implies \mathbb{H} \text{ or } \mathbb{O}$ (Quaternionic / Octonionic field)

---

## 2. Quantitative Algorithm Implementations

### Markowitz Convex Quadratic Programming (QP)
$$\min_{\mathbf{w}} \mathbf{w}^T \Sigma \mathbf{w} \quad \text{s.t.} \quad \mathbf{\mu}^T \mathbf{w} = r, \quad \mathbf{1}^T \mathbf{w} = 1, \quad \mathbf{w} \ge 0$$

### Black-Scholes Option Pricing & Greeks
$$C = S \cdot N(d_1) - K e^{-rT} N(d_2)$$
$$d_1 = \frac{\ln(S/K) + (r + \frac{1}{2}\sigma^2)T}{\sigma \sqrt{T}}, \quad d_2 = d_1 - \sigma \sqrt{T}$$

---

## 3. Backyard Ultra Loop Engineering

Agents running long-horizon tasks MUST follow the deterministic loop lifecycle:
1. **Idempotency**: Ensure operations can be safely re-run.
2. **Disk State Persistence**: Write state to `working_memory.md`, scratchpads, and git commits to survive token window truncation.
3. **Empirical Verification**: Never claim a task is completed without running tests or runtime verification commands.
