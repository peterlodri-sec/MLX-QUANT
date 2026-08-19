pub mod allocator;
pub mod tensor;
pub mod agx_doorbell;
pub mod polar_queue;
pub mod amd_mi300x;

use allocator::BumpAllocator;
use tensor::{Tensor, DType};
use polar_queue::PolarQueue;
use amd_mi300x::{AmdComputeRing, AmdPacket};
use std::time::Instant;

fn main() {
    println!("--- MLX-QUANT: The Cross-Continent Architecture ---");
    println!("Target Host: Apple Silicon (M1 Pro) -> AMD MI300X via PCIe\n");

    let allocator = BumpAllocator::new();

    // 1. Apple Silicon AGX (Polar Galaxy Queue)
    println!("=== APPLE SILICON (AGX) ===");
    let mut galaxy = PolarQueue::new(&allocator);
    galaxy.attach_arm("FP32_Weight_Stream");
    galaxy.attach_arm("INT4_Quantized_Activation_Stream");
    
    let weights = Tensor::new(vec![4096, 4096], DType::Float32, &allocator);
    let activations = Tensor::new(vec![4096, 4096], DType::Quantized4Bit, &allocator);
    galaxy.feed_tensor(0, weights);
    galaxy.feed_tensor(1, activations);
    
    let start_agx = Instant::now();
    galaxy.collapse_and_execute(1);
    println!("[+] AGX Hardware Doorbell Rung in {:?}", start_agx.elapsed());


    // 2. AMD MI300X PCIe Passthrough (The 4D Queue Bridge)
    println!("\n=== AMD MI300X (CDNA3) ===");
    
    let amd_doorbell_addr = 0xE000_0000;
    let amd_ring = AmdComputeRing::new(1024, amd_doorbell_addr, &allocator);
    println!("[*] Initialized AMD PM4 Compute Ring Buffer (1024 packets)");

    // Dispatch an MLX-QUANT Matrix Math kernel to the AMD GPU using PM4 Opcodes
    // Assuming the kernel is loaded at physical GPU VRAM address 0x4000_0000
    let kernel_vram_addr = 0x4000_0000;
    let grid_size = 256;
    let group_size = 64;
    
    let packet = AmdPacket::dispatch_kernel(grid_size, group_size, kernel_vram_addr);

    let start_amd = Instant::now();
    amd_ring.dispatch(packet);
    let amd_dur = start_amd.elapsed();

    println!("[+] AMD PACKET3_DISPATCH_DIRECT (Kernel Launch) Dispatched!");
    println!("[+] AMD PCIe Doorbell Latency: {:?}", amd_dur);
    println!("\nThe MI300X is now executing the INT4 MatMul kernel.");
}
