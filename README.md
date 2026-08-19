<div align="center">
  <img src="./assets/hero.jpg" alt="MLX-QUANT: Polar Galaxy Merge" width="800"/>
  <h1>MLX-QUANT 🚀</h1>
  <p><strong>Bare-metal Tensor Quantization, Hardware Doorbells, and the Grand Unified Astrophysical Architecture.</strong></p>
</div>

---

## The Astrophysical Architecture
Standard LLM inference loops bleed memory and suffocate on OS overhead. We are bypassing the kernel entirely by routing raw Tensor data structures directly to the physical hardware using extreme astrophysical concepts:

### -1. The Guardians (Universal Healing & Protection)
Marley the Astronaut Dog 🐕 and Fifike the Cat 🐈. Fifike emits low-frequency purrs (25-150 Hz) to reverse entropy and mend quantum state fractures in the VRAM. Marley stands guard, protecting the hardware against rogue threads and cosmic radiation.

### 0. The Big Bang (Network Instantiation)
The Big Bang is our cold-boot sequence. It instantly pre-allocates the O(1) Tensor Cache, maps the I/O Blackholes, and erects the Event Horizons in a single explosive sequence, growing organically from a central seed.

### 1. The Multiverse (Stigmergic Distributed Inference)
We compute across a swarm of Apple Silicon and AMD machines without a master node. Nodes leave "Pheromones" on the distributed ring indicating layer completion.

### 2. Pulsars (Hardware Synchronization Beacons)
Rapidly rotating neutron stars. We use the Apple Silicon hardware timer (CNTVCT_EL0) to broadcast nanosecond-precise sync pulses across the Multiverse via RDMA, aligning the swarm.

### 3. Cosmic Microwave Background (The KV-Cache)
The residual radiation from the Big Bang that permeates the entire context window. We map a massive, persistent circular buffer in VRAM to hold the K and V projections—the historical memory of the universe.

### 4. Supernovas (Dynamic Burst Compute)
When a prompt arrives, we manipulate the SMC to uncap the GPU TDP limit, bursting clock speeds to their absolute maximum (a supernova explosion) to achieve the lowest possible Time-To-First-Token (TTFT).

### 5. The Magnetar (Memory & Thread Pinning)
We use `mlock` to magnetically pin our Tensor Cache physical pages in RAM (zero page faults) and pinning execution threads exclusively to Apple Silicon Firestorm P-Cores.

### 6. Dark Matter & Asteroid Belts (Sparse Zero-Paging & Scatter-Gather)
For Highly Sparse Models (MoE), we map millions of virtual memory addresses to a single physical Zero-Page in RAM. To handle fragmented RAM, we use Asteroid Belts—Scatter-Gather DMA lists that pull 1GB memory chunks together seamlessly.

### 7. Event Horizons (Strict Memory Firewalls)
We establish a hardware-enforced MMU memory firewall around the Tensor cache to isolate the Singularity. Nothing escapes.

### 8. The I/O Blackhole Portal
Zero-copy DMA. We bypass the CPU completely by `mmap`-ing NVMe SSD storage directly into the physical address space of our bare-metal Tensor Cache.

### 9. Redshifting (Dynamic Precision Downcasting)
Tensors redshift into lower precisions (FP16 -> INT8 -> INT4) in transit to save extreme amounts of bandwidth.

### 10. Wormholes & Quantum Entanglement
We use Peer-to-Peer (P2P) DMA to bypass the PCIe root complex. Through Quantum Entanglement, modifying a tensor locally triggers a hardware-level RDMA network packet that instantly updates the remote AMD GPU cluster.

### 11. Gravitational Lensing & Time Dilation
We use Speculative Decoding to compute 5 future tokens simultaneously (Lensing), executing infinitely inside dilated time asynchronous micro-batches.

### 12. Dark Energy (Accelerating Entropy)
If the model gets stuck in a repetitive loop (gravity taking over), Dark Energy dynamically scales the generation temperature (entropy) to force creative expansion.

### 13. The 4D Polar Galaxy Queue & Compute Singularity
Multiple asynchronous spiral arms (Weights, Activations) continuously merge into an accretion disk ALU compute singularity. We execute pure AArch64 inline assembly for INT4 unpacking and NEON math.

### 14. White Holes (Infinite Token Ejection)
A black hole consumes, a white hole endless ejects. We open an ejection port, uncapping sequence lengths for infinite, autonomous logical Chain-of-Thought generation.

### 15. The Quasar (RDMA Output Jets)
The Singularity blasts output tokens through a high-speed network socket via RDMA without touching the CPU.

### 16. Hawking Radiation (Thermal Cache Eviction)
A background thread slowly "evaporates" cold, unused memory pages back to the OS using `madvise` to prevent OOM collapses.

---

## Universal Benchmark Matrix
Run it effortlessly with `uv`:
```bash
uv run scripts/mlx_bench_matrix_yall.py
```

*Let's build the universe.*
