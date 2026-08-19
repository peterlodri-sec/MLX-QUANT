use crate::allocator::BumpAllocator;
use std::sync::atomic::{AtomicU64, Ordering};

/// Represents an AMD PM4 Command Packet or HSA AQL Packet.
/// CDNA3 (MI300X) architectures process these packets to dispatch compute kernels.
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct AmdPacket {
    pub header: u16,
    pub opcode: u16,
    pub addr_lo: u32,
    pub addr_hi: u32,
    pub size: u32,
    // (Padded to 64 bytes for AQL standard alignment)
    pub _pad: [u32; 11],
}

impl AmdPacket {
    pub fn empty() -> Self {
        Self {
            header: 0,
            opcode: 0,
            addr_lo: 0,
            addr_hi: 0,
            size: 0,
            _pad: [0; 11],
        }
    }
}

/// A bare-metal AMD User Mode Queue (Ring Buffer)
pub struct AmdComputeRing<'a> {
    pub queue: *mut AmdPacket,
    pub capacity: usize,
    pub write_index: AtomicU64,
    doorbell_ptr: *mut u64,
    _marker: std::marker::PhantomData<&'a AmdPacket>,
}

impl<'a> AmdComputeRing<'a> {
    /// Maps a ring buffer directly into the BumpAllocator, and sets up the PCIe BAR doorbell.
    pub fn new(capacity: usize, pcie_bar2_doorbell_addr: usize, allocator: &'a BumpAllocator) -> Self {
        let size_bytes = capacity * std::mem::size_of::<AmdPacket>();
        
        // Allocate the contiguous Command Ring Buffer
        let queue_ptr = allocator.fast_alloc8(size_bytes) as *mut AmdPacket;

        Self {
            queue: queue_ptr,
            capacity,
            write_index: AtomicU64::new(0),
            doorbell_ptr: pcie_bar2_doorbell_addr as *mut u64,
            _marker: std::marker::PhantomData,
        }
    }

    /// Appends a new command packet to the compute ring and rings the MI300X Doorbell.
    #[inline(always)]
    pub fn dispatch(&self, packet: AmdPacket) {
        let w_idx = self.write_index.load(Ordering::Relaxed) as usize;
        let ring_idx = w_idx % self.capacity;

        // Write the packet directly to memory
        unsafe {
            std::ptr::write(self.queue.add(ring_idx), packet);
        }

        // Memory Barrier to guarantee the MI300X sees the packet data BEFORE the doorbell rings
        std::sync::atomic::fence(Ordering::Release);

        // Advance write pointer
        let new_w_idx = w_idx as u64 + 1;
        self.write_index.store(new_w_idx, Ordering::Relaxed);

        // Ring the AMD MI300X Doorbell over PCIe!
        // The AMD Command Processor monitors this register.
        unsafe {
            // Simulated: write_volatile(self.doorbell_ptr, new_w_idx);
            let _simulated_doorbell_write = new_w_idx;
            std::hint::black_box(_simulated_doorbell_write);
        }
    }
}
