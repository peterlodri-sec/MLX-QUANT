# Post-Quantum Cryptography: NIST Standards, Module Lattices & Google Infrastructure Alignment

*Dedicated Scaffold based on Google Security Blog (August 13, 2024) by Royal Hansen & Phil Venables.*

---

## 🏛️ Executive Summary & Milestone Overview

On August 13, 2024, the **National Institute of Standards and Technology (NIST)** officially released the finalized federal standards for **Post-Quantum Cryptography (PQC)**. Developed through an 8-year global competition started in 2016, these standards protect classical Internet communication against future decryption by **Cryptographically Relevant Quantum Computers (CRQCs)** running Shor's algorithm ($O(n^3)$ polynomial time factoring and discrete logarithms).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        NIST POST-QUANTUM CRYPTOGRAPHY STANDARDS                        │
├───────────────────┬───────────────────────────────┬────────────────────────────────────┤
│ STANDARD          │ FORMER NAME                   │ MATHEMATICAL FOUNDATION            │
├───────────────────┼───────────────────────────────┼────────────────────────────────────┤
│ FIPS 203 (ML-KEM) │ CRYSTALS-Kyber                │ Module Learning With Errors (M-LWE)│
│ FIPS 204 (ML-DSA) │ CRYSTALS-Dilithium            │ Module Short Integer Solution (M-SIS)
│ FIPS 205 (SLH-DSA)│ SPHINCS+                      │ Stateless Hash-Based Trees (SHA-2) │
└───────────────────┴───────────────────────────────┴────────────────────────────────────┘
```

---

## 🔒 1. Threats: Store Now, Decrypt Later (SNDL) & Firmware Forgery

1. **Store Now, Decrypt Later (SNDL)**: Adversaries passively record encrypted TLS 1.3/QUIC traffic streams today and store them. Once a CRQC becomes operational, RSA-2048/4090 and ECDH (P-256/Curve25519) keys are factored instantly via Shor's algorithm, exposing historical secrets.
2. **Firmware & Code Signing Forgery**: Long-lived hardware devices and IoT embedded chips must verify software updates using PQC digital signatures (ML-DSA or SLH-DSA) to prevent quantum-capable adversaries from forging vendor signatures.

---

## 📐 2. Mathematical Foundation: Module-Lattice Cryptography (M-LWE)

Module-Lattice Key Encapsulation (ML-KEM) rests on the hardness of the **Module Learning With Errors (M-LWE)** problem over polynomial rings $R_q = \mathbb{Z}_q[X] / (X^n + 1)$ with $n=256$ and prime modulus $q=3329$:

$$\mathbf{A} \mathbf{s} + \mathbf{e} = \mathbf{b} \pmod q$$

Where:
- $\mathbf{A} \in R_q^{k \times k}$ is a public matrix of polynomials.
- $\mathbf{s} \in R_q^k$ is a secret polynomial vector with small coefficients.
- $\mathbf{e} \in R_q^k$ is an error polynomial vector sampled from a centered binomial distribution.
- $\mathbf{b} \in R_q^k$ is the public key vector.

Solving for $\mathbf{s}$ given $(\mathbf{A}, \mathbf{b})$ is computationally intractable for both classical and quantum algorithms (Shortest Vector Problem in high-dimensional lattices).

---

## ⚡ 3. Google Infrastructure Implementation & Crypto Agility

### A. Chrome Desktop & Google Cloud TLS 1.3
In May 2024, **Google Chrome enabled ML-KEM by default** for TLS 1.3 and QUIC connections on desktop. Chrome pairs post-quantum key exchange with classical X25519 in a **Hybrid Key Exchange** (`X25519_MLKEM768`):

```
ClientHello ───► [ X25519 Public Key || ML-KEM-768 Ciphertext ] ───► Google Server
             ◄─── [ X25519 Shared Secret ⊕ ML-KEM Shared Secret ] ◄─── ServerHello
```

This hybrid construction guarantees that security holds if **either** X25519 or ML-KEM remains unbroken.

### B. Google Open Source & Standards Contributions
- **Google Tink**: Multi-language cryptographic library providing high-level, misuse-resistant PQC primitives in C++, Java, and Go.
- **IETF RFC Drafts**:
  - *Trust Expressions* (`draft-davidben-tls-trust-expr`)
  - *Merkle Tree Certificates* (`draft-davidben-tls-merkle-tree-certs`)
  - *Stateful Hash-Based Signatures* (`draft-wiggers-hbs-state`)

---

## 🌐 4. Alignment with AXIOM QUANT

On `axiomquant.org`, post-quantum lattice parameters map directly to **BitNet b1.58 Ternary Quantization** and **Erdős Phase Transitions**:

$$\text{Ternary Weights } w_q \in \{-1, 0, +1\} \quad \Longleftrightarrow \quad \text{Binomial Lattice Error } e_i \in \{-1, 0, +1\}$$

Lattice vector quantization exhibits a sharp phase transition at critical noise boundary $\sigma_c$, exactly mirroring the Erdős-Rényi threshold $p_c = \frac{\ln n}{n}$.
