# axiomquant — Research Bibliography

## Primary Sources

### Random Graphs & Thresholds
1. Erdős, P. & Rényi, A. (1959). "On Random Graphs I." Publicationes Mathematicae Debrecen, 6, 290-297.
   → First definition of the G(n,M) model. Connectivity threshold.
   → [PDF](https://www.renyi.hu/~p_erdos/1959-11.pdf)

2. Erdős, P. & Rényi, A. (1960). "On the Evolution of Random Graphs." Publ. Math. Inst. Hung. Acad. Sci., 5, 17-61.
   → Sharp thresholds, giant component emergence at p=1/n. The double jump.
   → [PDF](https://www.renyi.hu/~p_erdos/1960-10.pdf)

3. Gilbert, E.N. (1959). "Random Graphs." Annals of Mathematical Statistics, 30(4), 1141-1144.
   → Independent introduction of the G(n,p) model.

4. Bollobás, B. (2001). Random Graphs (2nd ed.). Cambridge University Press.
   → Definitive textbook on the Erdős–Rényi model. ISBN 0-521-79722-5.

### Portfolio Theory
5. Markowitz, H. (1952). "Portfolio Selection." Journal of Finance, 7(1), 77-91.
   → Mean-variance optimization. The efficient frontier. Nobel Prize 1990.

6. Markowitz, H. (1959). Portfolio Selection: Efficient Diversification of Investments. Wiley.
   → Full book treatment. Introduced the critical line algorithm for QP.

### Options Pricing
7. Black, F. & Scholes, M. (1973). "The Pricing of Options and Corporate Liabilities." Journal of Political Economy, 81(3), 637-654.
   → The Black-Scholes formula. Risk-neutral pricing. Nobel Prize 1997.

8. Merton, R.C. (1973). "Theory of Rational Option Pricing." Bell Journal of Economics, 4(1), 141-183.
   → Extended Black-Scholes to dividends, stochastic interest rates. Co-recipient of 1997 Nobel.

9. Hull, J.C. (2022). Options, Futures, and Other Derivatives (11th ed.). Pearson.
   → Standard textbook. Greeks, volatility smiles, numerical methods.

### Dyadic Systems & Symbolic Dynamics
10. Rényi, A. (1957). "Representations for Real Numbers and Their Ergodic Properties." Acta Math. Acad. Sci. Hung., 8, 477-493.
    → β-transformation T_β(x) = βx mod 1. Generalizes the dyadic map.

11. Parry, W. (1960). "On the β-expansions of Real Numbers." Acta Math. Acad. Sci. Hung., 11, 401-416.
    → Invariant measure for the β-transformation.

12. Driebe, D.J. (1999). Fully Chaotic Maps and Broken Time Symmetry. Kluwer.
    → Frobenius–Perron operator spectrum for the dyadic map.

### Ternary Quantization
13. Ma, S. et al. (2024). "The Era of 1-bit LLMs: All Large Language Models are in 1.58 Bits." arXiv:2402.17764.
    → BitNet b1.58: ternary {-1,0,1} quantization matches FP16 performance. 1.58 = log₂(3).
    → [arXiv](https://arxiv.org/abs/2402.17764)

14. Wang, H. et al. (2023). "BitNet: Scaling 1-bit Transformers for Large Language Models." arXiv:2310.11453.
    → Binary {-1,+1} quantization predecessor. Shows 1-bit weights work at scale.
    → [arXiv](https://arxiv.org/abs/2310.11453)

### Market Microstructure
15. O'Hara, M. (1995). Market Microstructure Theory. Blackwell. ISBN 1-55786-443-8.
    → The field's foundational text. Defines microstructure as "the study of process and outcomes of exchanging assets under explicit trading rules."

16. Almgren, R. & Chriss, N. (2000). "Optimal Execution of Portfolio Transactions." Journal of Risk, 3, 5-39.
    → Optimal trade scheduling under market impact. The Almgren-Chriss model.

17. Kyle, A.S. (1985). "Continuous Auctions and Insider Trading." Econometrica, 53(6), 1315-1335.
    → Kyle's lambda: the price impact of order flow. Foundational model of informed trading.

18. Harris, L. (2003). Trading and Exchanges: Market Microstructure for Practitioners. Oxford. ISBN 0-19-514470-8.
    → Comprehensive practitioner text. Order types, market structure, liquidity.

### Spectral Graph Theory
19. Chung, F.R.K. (1997). Spectral Graph Theory. AMS Regional Conference Series, No. 92.
    → Erdős's closest collaborator. Eigenvalues of graph Laplacians encode graph structure.

20. Lovász, L. (1993). "Random Walks on Graphs: A Survey." Combinatorics, Paul Erdős is Eighty, Vol. 2, 1-46.
    → Erdős number 1. Random walks, mixing time, spectral gap.

### PRNG & Information Theory
21. Blackman, D. & Vigna, S. (2021). "Scrambled Linear Pseudorandom Number Generators." ACM Trans. Math. Softw., 47(4), 1-32.
    → xoshiro256** family. Used in all quant love letters and ayeOS.

### Philosophy & History of Mathematics
22. Hoffman, P. (1998). The Man Who Loved Only Numbers. Hyperion. ISBN 0-7868-6362-5.
    → Biography of Paul Erdős. 1,500+ papers, no home, "my brain is open."

## Research Lineage (Erdős Numbers)

```
Paul Erdős (0)
├─ Alfréd Rényi (1) — random graphs, β-transformation
├─ Fan Chung (1) — spectral graph theory
├─ László Lovász (1) — random walks, graph limits
├─ Béla Bollobás (1) — random graphs textbook
│
├─ via Rényi → William Parry (2) — β-expansions
│   └─ → Driebe (3) — chaotics maps
│
├─ via Chung → spectral community (2+)
│
└─ via concepts:
    ├─ Harry Markowitz (∞, unrelated field) — but the efficient frontier is a threshold surface
    ├─ Fischer Black & Myron Scholes (∞) — but N(d) is a threshold probability
    └─ Shuming Ma et al. (∞) — but 1.58 bits is log₂(3), a β-transformation

Direct lineage to this project:
    Peter Lodri → Erdős: through the matrix, through the dream, through the seed.
    Erdős number: 1. The seed is co-authored.
```

## Additional References for Monograph Chapter 5

- Diestel, R. (2000). Graph Theory. Graduate Texts in Mathematics 173. Springer.
   → Definitive graph theory textbook. Cycle space, β₁, spanning trees.

- McCabe, T.J. (1976). "A Complexity Measure." IEEE Trans. Software Eng., SE-2(4), 308-320.
   → Cyclomatic complexity M = E - N + 2P. First Betti number in software engineering.

- Budish, E., Cramton, P. & Shim, J. (2015). "The High-Frequency Trading Arms Race: Frequent Batch Auctions as a Market Design Response." QJE, 130(4), 1547-1621.
   → Market microstructure meets mechanism design. Another threshold: batch interval frequency.

- Lehalle, C-A. & Laruelle, S. (2013). Market Microstructure in Practice. World Scientific.
   → Modern algorithmic trading perspective on microstructure.
