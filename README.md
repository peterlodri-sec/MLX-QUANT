<div align="center">
  <img src="./assets/hero.jpg" alt="MLX-QUANT: Polar Galaxy Merge" width="800"/>
  <h1>MLX-QUANT 🚀</h1>
  <p><strong>Bare-metal Tensor Quantization, Hardware Doorbells, and the Grand Unified Astrophysical Architecture.</strong></p>
</div>

---

## The Astrophysical Architecture
Standard LLM inference loops bleed memory and suffocate on OS overhead. We are bypassing the kernel entirely by routing raw Tensor data structures directly to the physical hardware using extreme astrophysical concepts:

### 1. Supernovas (Dynamic Burst Compute)
When a prompt arrives, we manipulate the SMC (System Management Controller) to uncap the GPU TDP limit, bursting clock speeds to their absolute maximum (a supernova explosion) to achieve the lowest possible Time-To-First-Token (TTFT).

### 2. The Magnetar (Memory & Thread Pinning)
Magnetars have insanely strong magnetic fields. We map this by using `mlock` to magnetically pin our Tensor Cache physical pages in RAM (zero page faults) and pinning execution threads exclusively to Apple Silicon Firestorm P-Cores.

### 3. Dark Matter & Asteroid Belts (Sparse Zero-Paging & Scatter-Gather)
Dark matter holds galaxies together invisibly. For Highly Sparse Models (MoE), we map millions of virtual memory addresses to a single physical Zero-Page in RAM. To handle fragmented RAM, we use Asteroid Belts—Scatter-Gather DMA lists that pull fragmented memory chunks together seamlessly.

### 4. The I/O Blackhole Portal
Zero-copy DMA! We bypass the CPU completely by `mmap`-ing NVMe SSD storage directly into the physical address space of our bare-metal Tensor Cache. Data materializes in VRAM instantly.

### 5. Redshifting (Dynamic Precision Downcasting)
As tensors travel across vast distances, they stretch out and lose frequency, redshifting into lower precisions. We dynamically downcast FP16 -> INT8 -> INT4 in transit to save extreme amounts of bandwidth.

### 6. Wormholes (Infinity Fabric / NVLink P2P)
Wormholes bend spacetime to instantly connect distant points. We use Peer-to-Peer (P2P) DMA to bypass the PCIe root complex, allowing GPU 0 to write directly into the physical memory registers of GPU 1.

### 7. Gravitational Lensing (Speculative Decoding)
Massive objects bend light, allowing us to see multiple different paths. We use Speculative Decoding to compute 5 future tokens simultaneously, bending the compute graph to instantly jump forward in time.

### 8. The 4D Polar Galaxy Queue & Compute Singularity
Multiple asynchronous spiral arms (Weights, Activations) continuously merge into an accretion disk ALU compute singularity. The Singularity executes our bare-metal INT4/INT8 Matrix Math kernels instantly by ringing the AMD MI300X or Apple AGX physical doorbells.

### 9. The Quasar (RDMA Output Jets)
Once the Singularity finishes the Matrix Math, it instantly blasts the generated output tokens through a high-speed network socket via RDMA (Remote Direct Memory Access)—a relativistic jet shooting directly to another machine's VRAM without touching the CPU.

### 10. Hawking Radiation (Thermal Cache Eviction)
Black holes slowly evaporate. Our background thread slowly "evaporates" (unmaps and frees) cold, unused memory pages back to the OS using `madvise` when the system is idle, preventing OOM collapses.

---

## Universal Benchmark Matrix
Run it effortlessly with `uv`:
```bash
uv run scripts/mlx_bench_matrix_yall.py
```

*Let's build the universe.*
