pub mod allocator;
pub mod tensor;
pub mod agx_doorbell;
pub mod polar_queue;

use allocator::BumpAllocator;
use tensor::{Tensor, DType};
use polar_queue::PolarQueue;
use std::time::Instant;

fn main() {
    println!("--- MLX-QUANT: The Polar Galaxy Merge ---");
    println!("Target Host: Apple Silicon (M1 Pro) Bare-Metal AGX\n");

    let allocator = BumpAllocator::new();
    let mut galaxy = PolarQueue::new(&allocator);

    // 1. Setup the Async Data Streams (Spiral Arms)
    galaxy.attach_arm("FP32_Weight_Stream");
    galaxy.attach_arm("INT4_Quantized_Activation_Stream");
    println!("[*] Attached 2 Spiral Arms to the Compute Core.");

    let start = Instant::now();

    // 2. Feed the spiral arms from our O(1) cache / allocator
    let weights = Tensor::new(vec![4096, 4096], DType::Float32, &allocator);
    let activations = Tensor::new(vec![4096, 4096], DType::Quantized4Bit, &allocator);
    
    galaxy.feed_tensor(0, weights);
    galaxy.feed_tensor(1, activations);

    println!("[*] Data streaming down the arms...");

    // 3. The Collapse (Execution)
    galaxy.collapse_and_execute(1);

    let duration = start.elapsed();
    
    println!("\n[+] Singularity Reached! Hardware Doorbell Rung.");
    println!("[+] Total queue latency (Alloc -> Stream -> Doorbell): {:?}", duration);
    println!("\nThe AGX GPU is now computing 16.7M parameters asynchronously.");
}
