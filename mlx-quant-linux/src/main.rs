pub mod allocator;
pub mod tensor;

use allocator::BumpAllocator;
use tensor::{Tensor, DType};
use std::time::Instant;

fn main() {
    println!("--- MLX-QUANT Tensor Caching ---");
    println!("Target Host: Apple Silicon (M1 Pro) Bare-Metal Mode\n");

    let allocator = BumpAllocator::new();

    println!("[*] Allocating Base KV Cache Tensor (1024 x 1024)...");
    let start = Instant::now();
    {
        let kv = Tensor::new(vec![1024, 1024], DType::Float16, &allocator);
        println!("[+] Initial Bump Allocation: {:?}", start.elapsed());
        println!("[+] Tensor dropped, pushed to append-only cache.");
    } // `kv` drops here, pushing its 2MB block to the cache!

    println!("\n[*] Requesting 10,000 identical KV Tensors in a loop...");
    let loop_start = Instant::now();
    for _ in 0..10_000 {
        // Because the block is in the cache, this is an instant O(1) pointer pop!
        // It never even touches the bump pointer or wastes memory.
        let _reused = Tensor::new(vec![1024, 1024], DType::Float16, &allocator);
    }
    let loop_time = loop_start.elapsed();
    
    println!("[+] Time for 10,000 cached tensor allocations: {:?}", loop_time);
    println!("[+] Average allocation latency: {:?}", loop_time / 10_000);
}
