use std::cell::Cell;
use std::cell::UnsafeCell;

const BUMP_HEAP_SIZE: usize = 64 * 1024 * 1024; // 64MB for tensors
struct HeapStorage(UnsafeCell<[u8; BUMP_HEAP_SIZE]>);
unsafe impl Sync for HeapStorage {}
static BUMP_HEAP: HeapStorage = HeapStorage(UnsafeCell::new([0; BUMP_HEAP_SIZE]));

const CACHE_SIZE: usize = 128;

pub struct BumpAllocator {
    ptr: Cell<usize>,
    
    // Append-only cache for recurring tensor blocks (size, pointer)
    cache: Cell<[(usize, usize); CACHE_SIZE]>,
    cache_len: Cell<usize>,
}

impl BumpAllocator {
    #[inline(always)]
    pub fn new() -> Self { 
        Self {
            ptr: Cell::new(BUMP_HEAP.0.get() as usize),
            cache: Cell::new([(0, 0); CACHE_SIZE]),
            cache_len: Cell::new(0),
        }
    }
    
    #[inline(always)]
    pub fn fast_alloc8(&self, size: usize) -> *mut u8 {
        // 1. Check the append-only cache for a block of the exact size
        let len = self.cache_len.get();
        if len > 0 {
            let mut current_cache = self.cache.get();
            // We search backwards to get the most recently cached block (LIFO)
            for i in (0..len).rev() {
                if current_cache[i].0 == size {
                    let ptr = current_cache[i].1;
                    
                    // Remove from cache (swap with last)
                    current_cache[i] = current_cache[len - 1];
                    self.cache.set(current_cache);
                    self.cache_len.set(len - 1);
                    
                    return ptr as *mut u8;
                }
            }
        }
        
        // 2. Fallback to O(1) Bump Allocation
        let p = self.ptr.get();
        let aligned = (p + 7) & !7;
        self.ptr.set(aligned + size);
        aligned as *mut u8
    }
    
    /// Returns a tensor block to the append-only cache for instant O(1) reuse
    #[inline(always)]
    pub fn cache_free(&self, ptr: *mut u8, size: usize) {
        let len = self.cache_len.get();
        if len < CACHE_SIZE {
            let mut current_cache = self.cache.get();
            current_cache[len] = (size, ptr as usize);
            self.cache.set(current_cache);
            self.cache_len.set(len + 1);
        }
    }
    
    #[inline(always)]
    pub fn reset(&self) {
        self.ptr.set(BUMP_HEAP.0.get() as usize);
        self.cache_len.set(0);
    }
}
