use crate::allocator::BumpAllocator;
use std::sync::atomic::{AtomicU64, Ordering};

/// Standard AMD PM4 Packet3 Opcodes (Mocked for MLX-QUANT)
#[repr(u16)]
#[derive(Debug, Clone, Copy)]
pub enum Pm4Opcode {
    Nop = 0x10,
    WriteData = 0x37,
    DispatchDirect = 0x15, // Used to dispatch compute kernels (MatMul)
    AcquireMem = 0x58,     // Cache synchronization / Memory barriers
}

/// Represents an AMD PM4 Command Packet
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

    /// Constructs a PACKET3_DISPATCH_DIRECT to launch an MLX-QUANT kernel
    pub fn dispatch_kernel(grid_size: u32, group_size: u32, kernel_addr: u64) -> Self {
        Self {
            header: 0xC000, // Packet3 Header Type
            opcode: Pm4Opcode::DispatchDirect as u16,
            addr_lo: (kernel_addr & 0xFFFFFFFF) as u32,
            addr_hi: (kernel_addr >> 32) as u32,
            size: grid_size * group_size,
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
        unsafe {
            let _simulated_doorbell_write = new_w_idx;
            std::hint::black_box(_simulated_doorbell_write);
        }
    }
}
