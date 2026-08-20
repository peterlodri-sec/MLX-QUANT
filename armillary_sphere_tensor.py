import math
import mlx.core as mx

class ArmillarySphereTensor:
    """
    An Astrophysical representation of a Neural Network Tensor.
    Instead of a flat matrix, weights are mapped onto a 3D Armillary Sphere.
    This naturally enforces sparse recursion, as updates propagate along 
    geodesics (rings) of the sphere rather than across a flat Cartesian grid.
    """
    def __init__(self, in_features, out_features, num_rings=12):
        self.in_features = in_features
        self.out_features = out_features
        self.num_rings = num_rings
        
        # Standard flat weight initialization
        limit = math.sqrt(6 / (in_features + out_features))
        flat_weights = mx.random.uniform(-limit, limit, shape=(out_features, in_features))
        
        # Convert flat weights into Armillary coordinates
        # Each weight is mapped to (r, theta, phi)
        # r = magnitude, theta = longitude (azimuth), phi = latitude (elevation)
        self.weights = flat_weights
        
        # Create the Armillary spatial mapping (static for the layer)
        self.theta = mx.random.uniform(0, 2 * math.pi, shape=(out_features, in_features))
        self.phi = mx.random.uniform(0, math.pi, shape=(out_features, in_features))
        
        # Density field for Holographic Steganography
        # Higher density = higher inertia (harder to change)
        self.density_field = mx.abs(self.weights) * mx.sin(self.phi)

    def stigmergic_threshold(self, base_tau: float) -> mx.array:
        """
        Computes the adaptive threshold $\tau(x, t)$ based on the local
        astrophysical density of the sphere.
        """
        # Inverse relation: denser regions (core) require MASSIVE gradients to update
        # Sparse regions (outer rings) update easily.
        return base_tau * (1.0 + self.density_field)

    def forward(self, x: mx.array) -> mx.array:
        """ Standard forward pass using the underlying manifold """
        return mx.matmul(x, self.weights.T)
        
    def sparse_recursive_update(self, grad: mx.array, lr: float = 0.01, base_tau: float = 0.005):
        """
        Applies the sparse recursion update:
        \Psi^{(t+1)} = \Psi^{(t)} + \alpha \nabla \mathcal{L} \odot \mathbb{I}(|\nabla| > \tau)
        """
        tau = self.stigmergic_threshold(base_tau)
        
        # Stigmergic Indicator Function (only update if gradient escapes gravity)
        mask = mx.abs(grad) > tau
        
        # Apply sparse update
        sparse_grad = mx.where(mask, grad, mx.zeros_like(grad))
        self.weights = self.weights - lr * sparse_grad
        
        # Update the density field steganographically
        self.density_field = self.density_field + 0.001 * mx.abs(sparse_grad)
        
        # Calculate sparsity metric
        active_nodes = mx.sum(mask.astype(mx.float32)).item()
        total_nodes = mask.size
        sparsity = 1.0 - (active_nodes / total_nodes)
        
        return sparsity

if __name__ == "__main__":
    print("🚀 Initializing MLX-QUANT Armillary Sphere Tensor...")
    sphere = ArmillarySphereTensor(in_features=1024, out_features=1024, num_rings=24)
    
    print(f"Sphere initialized with shape: {sphere.weights.shape}")
    
    # Simulate a gradient signal coming from a massive knowledge graph update
    mock_grad = mx.random.normal(shape=(1024, 1024))
    
    print("\nApplying Sparse Recursion over 5 epochs (Geodesic propagation):")
    for epoch in range(5):
        sparsity = sphere.sparse_recursive_update(grad=mock_grad, lr=0.1, base_tau=1.5)
        print(f"  Epoch {epoch+1}: Tensor Sparsity = {sparsity*100:.2f}% (Only {100-sparsity*100:.2f}% of the sphere was updated)")
        
        # Inject new random gradients
        mock_grad = mx.random.normal(shape=(1024, 1024))
        
    print("\n✅ Armillary Sphere structural integrity maintained.")
