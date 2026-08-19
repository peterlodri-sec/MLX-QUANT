use crate::allocator::BumpAllocator;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum DType {
    Float32,
    Float16,
    Int8,
    Quantized4Bit,
}

impl DType {
    pub fn size_bytes(&self) -> usize {
        match self {
            DType::Float32 => 4,
            DType::Float16 => 2,
            DType::Int8 => 1,
            DType::Quantized4Bit => 1,
        }
    }
}

pub struct Tensor<'a> {
    pub shape: Vec<usize>,
    pub dtype: DType,
    pub data: *mut u8,
    pub numel: usize,
    pub alloc_size: usize,
    allocator: &'a BumpAllocator,
}

impl<'a> Tensor<'a> {
    pub fn new(shape: Vec<usize>, dtype: DType, allocator: &'a BumpAllocator) -> Self {
        let mut numel = 1;
        for &dim in &shape {
            numel *= dim;
        }

        let mut alloc_size = numel * dtype.size_bytes();
        if dtype == DType::Quantized4Bit {
            alloc_size = (numel + 1) / 2;
        }

        let data_ptr = allocator.fast_alloc8(alloc_size);

        Self {
            shape,
            dtype,
            data: data_ptr,
            numel,
            alloc_size,
            allocator,
        }
    }

    pub fn zero(&mut self) {
        unsafe { std::ptr::write_bytes(self.data, 0, self.alloc_size) }
    }

    pub unsafe fn as_f32_slice_mut(&mut self) -> &mut [f32] {
        assert!(self.dtype == DType::Float32);
        std::slice::from_raw_parts_mut(self.data as *mut f32, self.numel)
    }
}

// When a tensor goes out of scope, it automatically pushes its block to the append-only cache!
impl<'a> Drop for Tensor<'a> {
    fn drop(&mut self) {
        self.allocator.cache_free(self.data, self.alloc_size);
    }
}
