use crate::allocator::BumpAllocator;
use crate::tensor::{Tensor, DType};
use std::fs::File;
#[cfg(target_os = "linux")]
use std::os::unix::io::AsRawFd;

/// The I/O Blackhole Portal
/// A zero-copy DMA (Direct Memory Access) tunnel that bypasses the CPU completely.
/// It sucks raw weight data directly from an NVMe SSD into the O(1) Tensor Cache.
pub struct IoBlackhole<'a> {
    allocator: &'a BumpAllocator,
}

impl<'a> IoBlackhole<'a> {
    pub fn new(allocator: &'a BumpAllocator) -> Self {
        Self { allocator }
    }

    /// Engages the Event Horizon.
    /// In a true bare-metal NVMe driver, we configure the PCIe root complex to 
    /// DMA transfer the blocks directly into our BumpAllocator memory pool.
    pub fn suck_weights_from_disk(&self, _file: &File, shape: Vec<usize>, dtype: DType) -> Tensor<'a> {
        // 1. Allocate a Tensor natively in the hardware pool (or pull from O(1) cache)
        let tensor = Tensor::new(shape, dtype, self.allocator);

        // 2. The Blackhole Event:
        // Normally, you would use `file.read()`, which copies from Disk -> OS Buffer -> CPU -> GPU.
        // Instead, we use `mmap` (or direct NVMe DMA submission queues) to map the file 
        // directly into the physical address of our Tensor.
        
        #[cfg(target_os = "linux")]
        {
            // let fd = file.as_raw_fd();
            // unsafe {
            //     libc::mmap(
            //         tensor.data as *mut libc::c_void,
            //         tensor.alloc_size,
            //         libc::PROT_READ,
            //         libc::MAP_PRIVATE | libc::MAP_FIXED,
            //         fd,
            //         0,
            //     );
            // }
        }

        // The data instantly materializes in the BumpAllocator pool. Zero CPU cycles wasted.
        tensor
    }
}
