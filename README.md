<div align="center">
  <img src="./assets/hero.jpg" alt="MLX-QUANT: Polar Galaxy Merge" width="800"/>
  <h1>MLX-QUANT 🚀</h1>
  <p><strong>Bare-metal Tensor Quantization, Hardware Doorbells, and the Grand Unified Astrophysical Architecture.</strong></p>
</div>

---

## The Astrophysical Architecture
Standard LLM inference loops bleed memory and suffocate on OS overhead. We are bypassing the kernel entirely by routing raw Tensor data structures directly to the physical hardware using extreme astrophysical concepts:

### 0. The Big Bang (Network Instantiation)
Before the computation can exist, it must be ignited. The Big Bang is our cold-boot sequence. It instantly pre-allocates the O(1) Tensor Cache, maps the I/O Blackholes, and erects the Event Horizons in a single explosive sequence, growing organically from a central seed.

### 1. The Multiverse (Stigmergic Distributed Inference)
Why run a 400B parameter model on a single node? We compute across a swarm of Apple Silicon and AMD machines without a master node. Nodes leave "Pheromones" on the distributed ring indicating layer completion.

### 2. Supernovas (Dynamic Burst Compute)
When a prompt arrives, we manipulate the SMC to uncap the GPU TDP limit, bursting clock speeds to their absolute maximum (a supernova explosion) to achieve the lowest possible Time-To-First-Token (TTFT).

### 3. The Magnetar (Memory & Thread Pinning)
We use `mlock` to magnetically pin our Tensor Cache physical pages in RAM (zero page faults) and pinning execution threads exclusively to Apple Silicon Firestorm P-Cores.

### 4. Dark Matter & Asteroid Belts (Sparse Zero-Paging & Scatter-Gather)
For Highly Sparse Models (MoE), we map millions of virtual memory addresses to a single physical Zero-Page in RAM. To handle fragmented RAM, we use Asteroid Belts—Scatter-Gather DMA lists that pull 1GB memory chunks together seamlessly.

### 5. Event Horizons (Strict Memory Firewalls)
A boundary in physical memory that nothing can cross. We establish a hardware-enforced MMU memory firewall around the Tensor cache to isolate the Singularity.

### 6. The I/O Blackhole Portal
Zero-copy DMA. We bypass the CPU completely by `mmap`-ing NVMe SSD storage directly into the physical address space of our bare-metal Tensor Cache.

### 7. Redshifting (Dynamic Precision Downcasting)
Tensors redshift into lower precisions (FP16 -> INT8 -> INT4) in transit to save extreme amounts of bandwidth.

### 8. Wormholes & Quantum Entanglement
We use Peer-to-Peer (P2P) DMA to bypass the PCIe root complex. Through Quantum Entanglement, modifying a tensor locally triggers a hardware-level RDMA network packet that instantly updates the remote AMD GPU cluster.

### 9. Gravitational Lensing & Time Dilation
We use Speculative Decoding to compute 5 future tokens simultaneously (Lensing), executing infinitely inside dilated time asynchronous micro-batches.

### 10. The 4D Polar Galaxy Queue & Compute Singularity
Multiple asynchronous spiral arms (Weights, Activations) continuously merge into an accretion disk ALU compute singularity, triggering physical hardware doorbells. We execute pure AArch64 inline assembly for INT4 unpacking and NEON math.

### 11. The Quasar (RDMA Output Jets)
The Singularity blasts output tokens through a high-speed network socket via RDMA without touching the CPU.

### 12. Hawking Radiation (Thermal Cache Eviction)
A background thread slowly "evaporates" cold, unused memory pages back to the OS using `madvise` to prevent OOM collapses.

---

## Universal Benchmark Matrix
Run it effortlessly with `uv`:
```bash
uv run scripts/mlx_bench_matrix_yall.py
```

*Let's build the universe.*
