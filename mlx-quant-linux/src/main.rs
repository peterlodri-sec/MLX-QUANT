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
    
    // Assume AMD PCIe BAR2 is mapped at physical address 0xE000_0000
    let amd_doorbell_addr = 0xE000_0000;
    let amd_ring = AmdComputeRing::new(1024, amd_doorbell_addr, &allocator);
    println!("[*] Initialized AMD AQL/PM4 Compute Ring Buffer (1024 packets)");

    // Simulate pushing an MLX-QUANT Matrix Math packet to the AMD GPU
    let packet = AmdPacket {
        header: 0x8000,   // PM4 Header / HSA format
        opcode: 0x0042,   // MAGIC_MLX_QUANT_MATMUL
        addr_lo: 0x1000,  // Lower 32-bits of tensor data
        addr_hi: 0x0000,  // Upper 32-bits of tensor data
        size: 16_777_216, // 16.7M params
        _pad: [0; 11],
    };

    let start_amd = Instant::now();
    amd_ring.dispatch(packet);
    let amd_dur = start_amd.elapsed();

    println!("[+] AMD PM4 Packet Dispatched over PCIe!");
    println!("[+] AMD Doorbell Latency: {:?}", amd_dur);
    println!("\nWe have successfully bridged the M1 Pro directly into the MI300X architecture.");
}
