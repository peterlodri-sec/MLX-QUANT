<div align="center">
  <img src="./assets/hero.jpg" alt="MLX-QUANT: Polar Galaxy Merge" width="800"/>
  <h1>MLX-QUANT 🚀</h1>
  <p><strong>Bare-metal Tensor Quantization, Hardware Doorbells, and the 4D Polar Galaxy Command Queue.</strong></p>
</div>

---

## The Vision
Standard LLM inference loops bleed memory and suffocate on OS overhead. We are bypassing the macOS kernel entirely by routing raw Tensor data structures directly to the physical AGX GPU Doorbell on Apple Silicon (M1 Pro) and the CDNA3 (MI300X) architectures over PCIe.

### Core Architecture
1. **O(1) Append-Only Tensor Cache**: Reuses temporary memory blocks instantly (130ns latency) via a lock-free bump allocator.
2. **The 4D Polar Galaxy Queue**: Computes are not flat. Multiple asynchronous spiral arms (FP32 weights, INT4 activations) continuously merge into an accretion disk ALU compute singularity.
3. **Hardware Doorbells**: Data streams directly into the `0x280004000` MMIO physical register (Apple Silicon), completely bypassing Metal APIs.
4. **AMD PM4 Opcodes**: Dispatches matrix math directly to the AMD MI300X using raw `PACKET3_DISPATCH_DIRECT` packets pushed directly into the hardware PCIe Doorbell mapped at `0xE000_0000`.

## Modules
- `mlx-quant-linux`: The bare-metal Rust scaffolding for the AGX Doorbell, AMD PM4 Ring Buffers, Spiral Arms, and `Tensor` data models.
- `hw-ultra`: The underlying low-level abstractions powering this layer (see the `8b-is/hw-ultra` crate).

*Let's build the universe.*
