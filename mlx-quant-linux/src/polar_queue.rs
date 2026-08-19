use crate::allocator::BumpAllocator;
use crate::tensor::Tensor;
use crate::agx_doorbell::AgxDoorbell;

/// The Spiral Arm represents a continuous, async stream of Tensor data.
pub struct SpiralArm<'a> {
    pub name: String,
    pub active_tensor: Option<Tensor<'a>>,
}

/// The 4D Polar Galaxy Queue
/// Represents multiple spiral arms of data merging into a single compute singularity.
pub struct PolarQueue<'a> {
    pub arms: Vec<SpiralArm<'a>>,
    allocator: &'a BumpAllocator,
    doorbell: AgxDoorbell,
}

impl<'a> PolarQueue<'a> {
    pub fn new(allocator: &'a BumpAllocator) -> Self {
        Self {
            arms: Vec::new(),
            allocator,
            doorbell: AgxDoorbell::new(),
        }
    }

    /// Add a new spiral arm (data stream) to the galaxy
    pub fn attach_arm(&mut self, name: &str) {
        self.arms.push(SpiralArm {
            name: name.to_string(),
            active_tensor: None,
        });
    }

    /// Feeds a tensor down a specific spiral arm towards the center
    pub fn feed_tensor(&mut self, arm_index: usize, tensor: Tensor<'a>) {
        if arm_index < self.arms.len() {
            self.arms[arm_index].active_tensor = Some(tensor);
        }
    }

    /// The Merge: Flushes the spiral arms into the compute cores by ringing the hardware doorbell.
    /// This is where the magic happens asynchronously.
    #[inline(always)]
    pub fn collapse_and_execute(&mut self, ring_id: u32) {
        // 1. Ensure all memory writes to the tensors in the spiral arms are fully visible 
        // to the GPU before ringing the doorbell (Memory Barrier)
        std::sync::atomic::fence(std::sync::atomic::Ordering::Release);

        // 2. Ring the hardware doorbell! The AGX GPU wakes up instantly and pulls the tensors.
        self.doorbell.ring(ring_id);
        
        // 3. (In a real driver, we'd wait for a GPU interrupt here, or poll a status register)
    }
}
