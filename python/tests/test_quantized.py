# Copyright © 2023 Apple Inc.

import unittest
from itertools import product

import mlx.core as mx
import mlx_tests


class TestQuantized(mlx_tests.MLXTestCase):
    def test_quantize_dequantize(self):
        w = mx.random.normal(shape=(128, 512))
        for gs in [32, 64, 128]:
            for b in [2, 3, 5, 6, 4, 8]:
                with self.subTest(gs=gs, b=b):
                    w_q, scales, biases = mx.quantize(w, group_size=gs, bits=b)
                    w_hat = mx.dequantize(w_q, scales, biases, gs, b)
                    errors = (w - w_hat).abs().reshape(*scales.shape, -1)
                    eps = 1e-6
                    self.assertTrue((errors <= (scales[..., None] + eps).abs()).all())

        # test quantize/dequantize 0s
        a = mx.zeros((256, 512))
        for gs in [32, 64, 128]:
            for b in [2, 3, 4, 5, 6, 8]:
                w_q, scales, biases = mx.quantize(a, gs, b)
                a_hat = mx.dequantize(w_q, scales, biases, gs, b)
                self.assertTrue(mx.all(a_hat == 0))

    def test_mxfp4_quantize_dequantize(self):
        lut = mx.array(
            [
                +0.0,
                +0.5,
                +1.0,
                +1.5,
                +2.0,
                +3.0,
                +4.0,
                +6.0,
                -0.0,
                -0.5,
                -1.0,
                -1.5,
                -2.0,
                -3.0,
                -4.0,
                -6.0,
            ]
        )
        w = lut[mx.random.randint(0, 16, shape=(128, 512))]
        w = w.reshape(-1, 32)
        w[:, 0] = 6
        w = (w + 3e-6).astype(mx.bfloat16)

        # Invalid bits / group size
        with self.assertRaises(ValueError):
            mx.quantize(w, bits=3, mode="mxfp4")

        with self.assertRaises(ValueError):
            mx.quantize(w, group_size=64, mode="mxfp4")

        w_q, scales = mx.quantize(w, mode="mxfp4")
        with self.assertRaises(ValueError):
            mx.dequantize(w_q, scales, bits=3, mode="mxfp4")

        with self.assertRaises(ValueError):
            mx.dequantize(w_q, scales, group_size=64, mode="mxfp4")

        # Invalid output type
        with self.assertRaises(ValueError):
            mx.dequantize(
                w_q, scales, group_size=32, bits=4, mode="mxfp4", dtype=mx.int32
            )

        w_hat = mx.dequantize(w_q, scales, mode="mxfp4")
        self.assertTrue(mx.allclose(w, w_hat, rtol=1e-5, atol=1e-5))

        # test quantize/dequantize 0s
        a = mx.zeros((256, 512))
        w_q, scales = mx.quantize(a, mode="mxfp4")
        w_hat = mx.dequantize(w_q, scales, mode="mxfp4")
        self.assertTrue(mx.all(w_hat == 0))

    def test_mxfp8_quantize_dequantize(self):
        w = 2 * mx.random.uniform(shape=(512, 32)) - 1
        w = w.astype(mx.bfloat16)

        # Invalid bits / group size
        with self.assertRaises(ValueError):
            mx.quantize(w, bits=3, mode="mxfp8")

        with self.assertRaises(ValueError):
            mx.quantize(w, group_size=32, bits=7, mode="mxfp8")
        w_q, scales = mx.quantize(w, group_size=32, mode="mxfp8")

        with self.assertRaises(ValueError):
            mx.dequantize(w_q, scales, group_size=16, mode="mxfp8")

        with self.assertRaises(ValueError):
            mx.dequantize(w_q, scales, bits=4, mode="mxfp8")

        w_hat = mx.dequantize(w_q, scales, mode="mxfp8")

        self.assertTrue(mx.allclose(w, w_hat, rtol=1e-1, atol=1e-1))

        # test quantize/dequantize 0s
        a = mx.zeros((256, 512))
        w_q, scales = mx.quantize(a, mode="mxfp8")
        w_hat = mx.dequantize(w_q, scales, mode="mxfp8")
        self.assertTrue(mx.all(w_hat == 0))

    def test_nvfp4_quantize_dequantize(self):
        lut = mx.array(
            [
                +0.0,
                +0.5,
                +1.0,
                +1.5,
                +2.0,
                +3.0,
                +4.0,
                +6.0,
                -0.0,
                -0.5,
                -1.0,
                -1.5,
                -2.0,
                -3.0,
                -4.0,
                -6.0,
            ]
        )
        w = lut[mx.random.randint(0, 16, shape=(128, 512))]
        w = w.reshape(-1, 16)
        w[:, 0] = 6
        w = (w + 3e-6).astype(mx.bfloat16)

        # Invalid bits / group size
        with self.assertRaises(ValueError):
            mx.quantize(w, bits=3, mode="nvfp4")

        with self.assertRaises(ValueError):
            mx.quantize(w, group_size=64, mode="nvfp4")

        w_q, scales = mx.quantize(w, mode="nvfp4")

        with self.assertRaises(ValueError):
            mx.dequantize(w_q, scales, bits=3, mode="nvfp4")

        with self.assertRaises(ValueError):
            mx.dequantize(w_q, scales, group_size=32, mode="nvfp4")

        w_hat = mx.dequantize(w_q, scales, mode="nvfp4")
        self.assertTrue(mx.allclose(w, w_hat, rtol=1e-5, atol=1e-5))

        # test quantize/dequantize 0s
        a = mx.zeros((256, 512))
        w_q, scales = mx.quantize(a, mode="nvfp4")
        w_hat = mx.dequantize(w_q, scales, mode="nvfp4")
        self.assertTrue(mx.all(w_hat == 0))

        # Test nvfp4 quantize/dequantize with tensor-scale global_scale
        # currently supported only on cpu and cuda
        if not mx.metal.is_available():
            global_scale = w.abs().max().astype(mx.float32)
        else:
            global_scale = None

        w_q, scales = mx.quantize(w, mode="nvfp4", global_scale=global_scale)
        w_hat = mx.dequantize(
            w_q, scales, group_size=16, bits=4, mode="nvfp4", global_scale=global_scale
        )
        self.assertTrue(mx.allclose(w, w_hat, rtol=1e-5, atol=1e-5))

    def ternary_round_clip_reference(self, w, group_size):
        # BitNet b1.58 (arXiv:2402.17764): scale = mean(|w|) per group,
        # code = RoundClip(w / scale, -1, 1). Independent re-derivation of
        # the math ternary_quantize/ternary_dequantize implement, used here
        # as an oracle rather than re-testing the implementation against
        # itself.
        shape = w.shape
        grouped = w.reshape(-1, shape[-1] // group_size, group_size)
        scale = mx.maximum(mx.abs(grouped).mean(axis=-1, keepdims=True), 1e-7)
        code = mx.clip(mx.round(grouped / scale), -1, 1)
        dequant = (code * scale).reshape(shape)
        return dequant

    def assert_ternary_gpu_allclose(
        self, a, b, atol=1e-4, rtol=1e-4, max_bad_frac=0.02
    ):
        # Unlike affine/fp's min/max-based scale (order-independent -- min
        # and max never disagree regardless of reduction order), ternary's
        # scale is mean(|w|), a sum, and floating-point addition is not
        # associative. The GPU kernel's simd_sum (a parallel tree
        # reduction) can legitimately disagree with this file's
        # sequentially-computed reference sum in the last bit or two. That
        # almost never matters -- except for a weight whose w/scale ratio
        # lands almost exactly on a round()-tie (near +/-0.5), where the
        # tiniest scale difference flips which side it rounds to. Measured
        # empirically: ~2% of random seeds trigger this, affecting exactly
        # one weight out of hundreds of thousands each time. This is a
        # real, bounded, well-understood numerical property, not a logic
        # bug -- CPU never exhibits it (0/500 seeds in the same sweep),
        # confirming it's specifically about GPU's reduction order. Assert
        # closeness allows a tiny fraction of outliers instead of requiring
        # bit-exact agreement with an independently-recomputed reference.
        close = mx.abs(a - b) <= (atol + rtol * mx.abs(b))
        bad_frac = 1.0 - float(mx.mean(close.astype(mx.float32)))
        self.assertLess(
            bad_frac, max_bad_frac, f"{bad_frac:.4%} of elements exceeded tolerance"
        )

    def test_ternary_quantize_dequantize(self):
        # Stage 1 ternary support is CPU-only -- pin the stream explicitly
        # so this test is correct regardless of the machine's default
        # device (e.g. a Metal-enabled build defaults to gpu).
        with mx.stream(mx.cpu):
            for shape, gs in [((128, 512), 64), ((32, 256), 32), ((8, 64), 64)]:
                with self.subTest(shape=shape, gs=gs):
                    w = mx.random.normal(shape=shape)
                    w_q, scales = mx.quantize(w, group_size=gs, bits=2, mode="ternary")
                    w_hat = mx.dequantize(
                        w_q, scales, group_size=gs, bits=2, mode="ternary"
                    )
                    w_ref = self.ternary_round_clip_reference(w, gs)
                    self.assertTrue(mx.allclose(w_hat, w_ref, atol=1e-6))

            # Invalid bits
            with self.assertRaises(ValueError):
                mx.quantize(mx.random.normal(shape=(8, 64)), bits=3, mode="ternary")

            # No biases allowed
            w_q, scales = mx.quantize(mx.random.normal(shape=(8, 64)), mode="ternary")
            with self.assertRaises(ValueError):
                mx.dequantize(
                    w_q,
                    scales,
                    biases=mx.zeros_like(scales),
                    bits=2,
                    mode="ternary",
                )

            # test quantize/dequantize 0s
            a = mx.zeros((256, 512))
            w_q, scales = mx.quantize(a, mode="ternary")
            w_hat = mx.dequantize(w_q, scales, mode="ternary")
            self.assertTrue(mx.all(w_hat == 0))

            # Packed storage is smaller than the unquantized weight -- the
            # point of a native (not just simulated) quantization format.
            w = mx.random.normal(shape=(4096, 4096))
            w_q, scales = mx.quantize(w, group_size=64, bits=2, mode="ternary")
            mx.eval(w_q, scales)
            self.assertLess(w_q.nbytes + scales.nbytes, w.nbytes)

        # The GPU (Metal/CUDA) quantize/dequantize path is backed by a real
        # kernel (mlx/backend/metal/kernels/ternary_quantized.h) -- verify
        # it round-trips against the same independent reference used above.
        # Exercise every (T, group_size) combination the .metal file actually
        # instantiates (float/float16_t/bfloat16_t x gs 32/64/128), not just
        # the float32 default -- group_size=128 in particular takes a
        # structurally distinct path in ternary_quantize (values_per_reduce
        # == pack_factor, so the simd_shuffle_down combine loop runs zero
        # iterations, unlike gs=32/64).
        if mx.metal.is_available():
            with mx.stream(mx.gpu):
                for shape, gs in [
                    ((128, 512), 32),
                    ((128, 512), 64),
                    ((128, 512), 128),
                    ((32, 256), 32),
                    ((8, 64), 64),
                ]:
                    with self.subTest(shape=shape, gs=gs, device="gpu"):
                        w = mx.random.normal(shape=shape)
                        w_q, scales = mx.quantize(
                            w, group_size=gs, bits=2, mode="ternary"
                        )
                        w_hat = mx.dequantize(
                            w_q, scales, group_size=gs, bits=2, mode="ternary"
                        )
                        w_ref = self.ternary_round_clip_reference(w, gs)
                        self.assert_ternary_gpu_allclose(w_hat, w_ref, atol=1e-6)

                for dtype in [mx.float16, mx.bfloat16]:
                    with self.subTest(dtype=dtype, device="gpu"):
                        w = mx.random.normal(shape=(128, 512)).astype(dtype)
                        w_q, scales = mx.quantize(
                            w, group_size=64, bits=2, mode="ternary"
                        )
                        w_hat = mx.dequantize(
                            w_q, scales, group_size=64, bits=2, mode="ternary"
                        )
                        w_ref = self.ternary_round_clip_reference(
                            w.astype(mx.float32), 64
                        ).astype(dtype)
                        self.assert_ternary_gpu_allclose(w_hat, w_ref, atol=2e-2)

    def test_ternary_qmm(self):
        with mx.stream(mx.cpu):
            for M, K, N, gs, transpose in [
                (1, 64, 32, 64, True),
                (8, 128, 256, 64, True),
                (5, 256, 17, 64, True),
                (1, 64, 64, 64, False),
                (8, 128, 256, 64, False),
            ]:
                with self.subTest(M=M, K=K, N=N, gs=gs, transpose=transpose):
                    x = mx.random.normal(shape=(M, K))
                    w_shape = (N, K) if transpose else (K, N)
                    w = mx.random.normal(shape=w_shape)
                    w_q, scales = mx.quantize(w, group_size=gs, bits=2, mode="ternary")
                    w_hat = self.ternary_round_clip_reference(w, gs)
                    y_q = mx.quantized_matmul(
                        x,
                        w_q,
                        scales,
                        group_size=gs,
                        bits=2,
                        mode="ternary",
                        transpose=transpose,
                    )
                    y_ref = (x @ w_hat.T) if transpose else (x @ w_hat)
                    self.assertTrue(mx.allclose(y_q, y_ref, atol=1e-4, rtol=1e-4))

            # Batched activations against a single (unbatched) weight matrix.
            x = mx.random.normal(shape=(3, 5, 128))
            w = mx.random.normal(shape=(64, 128))
            w_q, scales = mx.quantize(w, group_size=64, bits=2, mode="ternary")
            w_hat = self.ternary_round_clip_reference(w, 64)
            y_q = mx.quantized_matmul(
                x, w_q, scales, group_size=64, bits=2, mode="ternary", transpose=True
            )
            y_ref = x @ w_hat.T
            self.assertTrue(mx.allclose(y_q, y_ref, atol=1e-4, rtol=1e-4))

            # Gather-based (MoE) ternary matmul: composed from
            # ternary_dequantize + the existing dense gather_mm op (see
            # mlx/ops.cpp), not a native kernel -- test_gather_qmm's own
            # mode="ternary" entry covers this more thoroughly against the
            # same mx.gather_mm(dequantized weights) reference every other
            # mode there uses; this just checks it works at all here.
            w = mx.random.normal(shape=(4, 64, 128))
            w_q, scales = mx.quantize(w, group_size=64, bits=2, mode="ternary")
            x = mx.random.normal(shape=(2, 128))
            indices = mx.array([0, 1])
            y_q = mx.gather_qmm(
                x,
                w_q,
                scales,
                rhs_indices=indices,
                group_size=64,
                bits=2,
                mode="ternary",
                transpose=True,
            )
            w_hat = self.ternary_round_clip_reference(w, 64)
            y_ref = mx.gather_mm(x, w_hat.swapaxes(-1, -2), rhs_indices=indices)
            self.assertTrue(mx.allclose(y_q, y_ref, atol=1e-4, rtol=1e-4))

        # GPU quantized_matmul composes dequantize + dense matmul rather
        # than a fused kernel (see mlx/ops.cpp) -- verify it still matches
        # the same independent reference used above, including gs=128
        # (structurally distinct in ternary_quantize, see the comment in
        # test_ternary_quantize_dequantize) and non-float32 dtypes.
        if mx.metal.is_available():
            with mx.stream(mx.gpu):
                for M, K, N, gs, transpose in [
                    (1, 64, 32, 64, True),
                    (8, 128, 256, 64, True),
                    (5, 256, 17, 64, True),
                    (8, 256, 32, 128, True),
                    (1, 64, 64, 64, False),
                    (8, 128, 256, 64, False),
                ]:
                    with self.subTest(
                        M=M, K=K, N=N, gs=gs, transpose=transpose, device="gpu"
                    ):
                        x = mx.random.normal(shape=(M, K))
                        w_shape = (N, K) if transpose else (K, N)
                        w = mx.random.normal(shape=w_shape)
                        w_q, scales = mx.quantize(
                            w, group_size=gs, bits=2, mode="ternary"
                        )
                        w_hat = self.ternary_round_clip_reference(w, gs)
                        y_q = mx.quantized_matmul(
                            x,
                            w_q,
                            scales,
                            group_size=gs,
                            bits=2,
                            mode="ternary",
                            transpose=transpose,
                        )
                        y_ref = (x @ w_hat.T) if transpose else (x @ w_hat)
                        self.assert_ternary_gpu_allclose(y_q, y_ref)

                for dtype in [mx.float16, mx.bfloat16]:
                    with self.subTest(dtype=dtype, device="gpu"):
                        x = mx.random.normal(shape=(8, 128)).astype(dtype)
                        w = mx.random.normal(shape=(256, 128)).astype(dtype)
                        w_q, scales = mx.quantize(
                            w, group_size=64, bits=2, mode="ternary"
                        )
                        w_hat = self.ternary_round_clip_reference(
                            w.astype(mx.float32), 64
                        ).astype(dtype)
                        y_q = mx.quantized_matmul(
                            x,
                            w_q,
                            scales,
                            group_size=64,
                            bits=2,
                            mode="ternary",
                            transpose=True,
                        )
                        y_ref = x @ w_hat.T
                        self.assert_ternary_gpu_allclose(
                            y_q, y_ref, atol=2e-2, rtol=2e-2
                        )

    def test_ternary_qmv_fast(self):
        # The fused ternary_qmv_fast GPU kernel only engages for a specific
        # shape (mlx/ops.cpp): non-batched weights, transpose=True, N%8==0,
        # and K%1024==0 -- 1024 is ternary_qmv_fast_impl's own block_size
        # (values_per_thread(32) * SIMD_SIZE(32)), NOT affine/fp's familiar
        # 512, since ternary's bits=2 pack factor is 2x theirs. A first
        # version of this gate used %512 by mistake, which let K=512 (not
        # actually a multiple of the kernel's real block_size) through and
        # caused out-of-bounds reads for half of each simdgroup's lanes --
        # caught here by testing more than one group size on a fixed K,
        # since group_size=64 alone happened to still look correct by luck.
        if not mx.metal.is_available():
            return
        with mx.stream(mx.gpu):
            for M, K, N, gs in [
                (1, 1024, 512, 32),
                (1, 1024, 512, 64),
                (1, 1024, 512, 128),
                (4, 1024, 256, 64),
                (1, 2048, 8, 64),
            ]:
                with self.subTest(M=M, K=K, N=N, gs=gs, path="fused"):
                    x = mx.random.normal(shape=(M, K))
                    w = mx.random.normal(shape=(N, K))
                    w_q, scales = mx.quantize(w, group_size=gs, bits=2, mode="ternary")
                    w_hat = self.ternary_round_clip_reference(w, gs)
                    y_q = mx.quantized_matmul(
                        x,
                        w_q,
                        scales,
                        group_size=gs,
                        bits=2,
                        mode="ternary",
                        transpose=True,
                    )
                    y_ref = x @ w_hat.T
                    self.assert_ternary_gpu_allclose(y_q, y_ref)

            # K=512 divides affine/fp's %512 gate but not ternary_qmv_fast's
            # real %1024 block_size -- must fall through to the compose
            # fallback, not the fused kernel, and still be correct.
            for gs in [32, 64, 128]:
                with self.subTest(K=512, gs=gs, path="compose (K not %1024)"):
                    x = mx.random.normal(shape=(4, 512))
                    w = mx.random.normal(shape=(512, 512))
                    w_q, scales = mx.quantize(w, group_size=gs, bits=2, mode="ternary")
                    w_hat = self.ternary_round_clip_reference(w, gs)
                    y_q = mx.quantized_matmul(
                        x,
                        w_q,
                        scales,
                        group_size=gs,
                        bits=2,
                        mode="ternary",
                        transpose=True,
                    )
                    y_ref = x @ w_hat.T
                    self.assert_ternary_gpu_allclose(y_q, y_ref)

            # N not a multiple of 8 -- falls through to compose.
            with self.subTest(path="compose (N not %8)"):
                x = mx.random.normal(shape=(2, 1024))
                w = mx.random.normal(shape=(17, 1024))
                w_q, scales = mx.quantize(w, group_size=64, bits=2, mode="ternary")
                w_hat = self.ternary_round_clip_reference(w, 64)
                y_q = mx.quantized_matmul(
                    x,
                    w_q,
                    scales,
                    group_size=64,
                    bits=2,
                    mode="ternary",
                    transpose=True,
                )
                y_ref = x @ w_hat.T
                self.assert_ternary_gpu_allclose(y_q, y_ref)

            # Batched weights (w.ndim() > 2) -- falls through to compose.
            with self.subTest(path="compose (batched weights)"):
                x = mx.random.normal(shape=(4, 2, 1024))
                w = mx.random.normal(shape=(4, 512, 1024))
                w_q, scales = mx.quantize(w, group_size=64, bits=2, mode="ternary")
                w_hat = self.ternary_round_clip_reference(w, 64)
                y_q = mx.quantized_matmul(
                    x,
                    w_q,
                    scales,
                    group_size=64,
                    bits=2,
                    mode="ternary",
                    transpose=True,
                )
                y_ref = x @ mx.swapaxes(w_hat, -1, -2)
                self.assert_ternary_gpu_allclose(y_q, y_ref)

    def test_ternary_qvm(self):
        # The fused ternary_qvm GPU kernel covers transpose=False,
        # non-batched weights (mlx/ops.cpp gates on w.ndim() == 2 and
        # N % 32 == 0 -- ternary_qvm_impl's values_per_thread is fixed at
        # 32 regardless of group_size, and its final write loop has no
        # per-column bounds check). N % 32 == 0 is actually guaranteed by
        # mx.quantize itself for any valid ternary w here: group_size is
        # always one of {32, 64, 128} (all multiples of 32) and quantize
        # requires N % group_size == 0, so N % 32 == 0 follows -- there is
        # no reachable "N not %32" fallback case to test, unlike
        # ternary_qmv_fast's K%1024 gate.
        if not mx.metal.is_available():
            return
        with mx.stream(mx.gpu):
            for M, K, N, gs in [
                (1, 512, 512, 64),
                (1, 300, 64, 64),
                (4, 1024, 256, 32),
                (8, 200, 32, 32),
                (1, 1000, 128, 128),
                (1, 33, 32, 32),
            ]:
                with self.subTest(M=M, K=K, N=N, gs=gs, path="fused"):
                    x = mx.random.normal(shape=(M, K))
                    w = mx.random.normal(shape=(K, N))
                    w_q, scales = mx.quantize(w, group_size=gs, bits=2, mode="ternary")
                    w_hat = self.ternary_round_clip_reference(w, gs)
                    y_q = mx.quantized_matmul(
                        x,
                        w_q,
                        scales,
                        group_size=gs,
                        bits=2,
                        mode="ternary",
                        transpose=False,
                    )
                    y_ref = x @ w_hat
                    self.assert_ternary_gpu_allclose(y_q, y_ref)

            # Batched weights (w.ndim() > 2) -- falls through to compose.
            with self.subTest(path="compose (batched weights)"):
                x = mx.random.normal(shape=(4, 2, 128))
                w = mx.random.normal(shape=(4, 128, 256))
                w_q, scales = mx.quantize(w, group_size=64, bits=2, mode="ternary")
                w_hat = self.ternary_round_clip_reference(w, 64)
                y_q = mx.quantized_matmul(
                    x,
                    w_q,
                    scales,
                    group_size=64,
                    bits=2,
                    mode="ternary",
                    transpose=False,
                )
                y_ref = x @ w_hat
                self.assert_ternary_gpu_allclose(y_q, y_ref)

    def test_ternary_qmv_general(self):
        # The general, bounds-checked ternary_qmv GPU kernel handles any K
        # (a safe zero-padded/partial-byte tail for the K-block remainder)
        # and any N (a "slide the last tile back" trick for N not a
        # multiple of 8) for transpose=True, non-batched weights -- it's
        # what mlx::quantized_matmul falls to whenever ternary_qmv_fast's
        # exact-multiple (N%8==0, K%1024==0) precondition doesn't hold.
        # Only batched weights still compose. Covers both of
        # ternary_qmv_impl's branches: out_vec_size < 8 (small-N) and the
        # "used_out_row" tile-shift for out_vec_size >= 8 but not %8.
        if not mx.metal.is_available():
            return
        with mx.stream(mx.gpu):
            for M, K, N, gs in [
                (1, 512, 512, 64),  # K%512==0 but not %1024 -- was the bug shape
                (1, 64, 64, 64),  # tiny K
                (1, 192, 4, 64),  # small-N branch (N=4 < 8)
                (8, 640, 13, 64),  # used_out_row branch (N=13, not %8)
                (1, 1024, 8, 64),  # K%1024==0 but N==8 exactly (boundary)
                (1, 96, 3, 32),  # tiny everything, N=3 < 8
                (4, 320, 21, 32),  # N not %8, K not a multiple of 512
                (1, 1056, 1, 32),  # N=1, extreme small-N
            ]:
                with self.subTest(M=M, K=K, N=N, gs=gs, path="fused-general"):
                    x = mx.random.normal(shape=(M, K))
                    w = mx.random.normal(shape=(N, K))
                    w_q, scales = mx.quantize(w, group_size=gs, bits=2, mode="ternary")
                    w_hat = self.ternary_round_clip_reference(w, gs)
                    y_q = mx.quantized_matmul(
                        x,
                        w_q,
                        scales,
                        group_size=gs,
                        bits=2,
                        mode="ternary",
                        transpose=True,
                    )
                    y_ref = x @ w_hat.T
                    self.assert_ternary_gpu_allclose(y_q, y_ref)

            # Batched weights (w.ndim() > 2) -- the only remaining compose case
            # for transpose=True now that ternary_qmv covers everything else.
            with self.subTest(path="compose (batched weights)"):
                x = mx.random.normal(shape=(4, 2, 128))
                w = mx.random.normal(shape=(4, 256, 128))
                w_q, scales = mx.quantize(w, group_size=64, bits=2, mode="ternary")
                w_hat = self.ternary_round_clip_reference(w, 64)
                y_q = mx.quantized_matmul(
                    x,
                    w_q,
                    scales,
                    group_size=64,
                    bits=2,
                    mode="ternary",
                    transpose=True,
                )
                y_ref = x @ mx.swapaxes(w_hat, -1, -2)
                self.assert_ternary_gpu_allclose(y_q, y_ref)

    def test_ternary_qmm_gemm(self):
        # The tiled GEMM ternary_qmm_t GPU kernel (mirrors quantized.h's
        # QuantizedBlockLoader/qmm_t_impl/affine_qmm_t) engages for
        # transpose=True, non-batched weights, M >= 32 (mlx/ops.cpp) --
        # decodes each weight group once per BM(32)-row tile and reuses it
        # across all 32 rows via threadgroup memory, unlike ternary_qmv*
        # which re-decodes per row. Covers aligned and unaligned M and N
        # (M/N not multiples of 32 exercise load_safe/store_result_safe).
        #
        # At large K (e.g. 4096, a 128-iteration accumulation), a single
        # mis-quantized weight from the same simd_sum-vs-sequential-sum
        # tie-breaking property documented in assert_ternary_gpu_allclose
        # now shows up in EVERY one of the M rows that share that weight
        # column (GEMV-style kernels only ever showed it in one row, since
        # M=1 there) -- confirmed by direct inspection (traced a worst-case
        # run down to exactly 1 mismatched weight per affected output row,
        # affecting 2 of 4096 columns across all rows). assert_ternary_gpu_
        # allclose's bounded-outlier-fraction check already accounts for
        # this scaling correctly (0.05% bad vs a 2% threshold), so no
        # special-casing is needed here, just the same helper as everywhere
        # else in this file.
        if not mx.metal.is_available():
            return
        with mx.stream(mx.gpu):
            for M, K, N, gs in [
                (32, 512, 512, 64),
                (64, 1024, 256, 64),
                (128, 4096, 4096, 64),  # large-K accumulation, see above
                (33, 512, 512, 32),
                (32, 64, 32, 64),
                (100, 320, 640, 32),
                (32, 96, 17, 32),  # N not %32 -- unaligned_N path
                (37, 96, 48, 32),  # M and N both not %32 -- fully unaligned
                (32, 128, 128, 128),
            ]:
                with self.subTest(M=M, K=K, N=N, gs=gs, path="qmm_t"):
                    x = mx.random.normal(shape=(M, K))
                    w = mx.random.normal(shape=(N, K))
                    w_q, scales = mx.quantize(w, group_size=gs, bits=2, mode="ternary")
                    w_hat = self.ternary_round_clip_reference(w, gs)
                    y_q = mx.quantized_matmul(
                        x,
                        w_q,
                        scales,
                        group_size=gs,
                        bits=2,
                        mode="ternary",
                        transpose=True,
                    )
                    y_ref = x @ w_hat.T
                    self.assert_ternary_gpu_allclose(y_q, y_ref)

            # M just under the 32 threshold -- must use ternary_qmv, not
            # ternary_qmm_t, and still be correct.
            with self.subTest(M=31, path="qmv (below qmm_t threshold)"):
                x = mx.random.normal(shape=(31, 1024))
                w = mx.random.normal(shape=(512, 1024))
                w_q, scales = mx.quantize(w, group_size=64, bits=2, mode="ternary")
                w_hat = self.ternary_round_clip_reference(w, 64)
                y_q = mx.quantized_matmul(
                    x,
                    w_q,
                    scales,
                    group_size=64,
                    bits=2,
                    mode="ternary",
                    transpose=True,
                )
                y_ref = x @ w_hat.T
                self.assert_ternary_gpu_allclose(y_q, y_ref)

            # Batched weights with large M -- ternary_qmm_t is non-batched
            # only, must still fall through to compose.
            with self.subTest(path="compose (batched weights, large M)"):
                x = mx.random.normal(shape=(4, 40, 1024))
                w = mx.random.normal(shape=(4, 512, 1024))
                w_q, scales = mx.quantize(w, group_size=64, bits=2, mode="ternary")
                w_hat = self.ternary_round_clip_reference(w, 64)
                y_q = mx.quantized_matmul(
                    x,
                    w_q,
                    scales,
                    group_size=64,
                    bits=2,
                    mode="ternary",
                    transpose=True,
                )
                y_ref = x @ mx.swapaxes(w_hat, -1, -2)
                self.assert_ternary_gpu_allclose(y_q, y_ref)

    def test_qqmv(self):
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        tests = product(
            [256, 512, 67],  # M
            [64, 256],  # N
            ["nvfp4", "mxfp8"],  # mode
        )
        for M, N, mode in tests:
            with self.subTest(shape=(M, N), mode=mode):
                x_shape = (1, N)
                w_shape = (M, N)

                # TODO: Fix qmv with global scale in Metal/CPU backends.
                has_global_scale = (
                    mode == "nvfp4"
                    and mx.cuda.is_available()
                    and mx.default_device() == mx.gpu
                )

                x = mx.random.normal(shape=x_shape, key=k1)
                global_scale_x = mx.max(mx.abs(x)) if has_global_scale else None
                x_hat = mx.dequantize(
                    *mx.quantize(x, mode=mode, global_scale=global_scale_x),
                    mode=mode,
                    dtype=mx.float32,
                    global_scale=global_scale_x,
                )

                w = mx.random.normal(shape=w_shape, key=k2)
                global_scale_w = mx.max(mx.abs(w)) if has_global_scale else None
                w_q, scales = mx.quantize(w, mode=mode, global_scale=global_scale_w)
                w_hat = mx.dequantize(
                    w_q,
                    scales,
                    mode=mode,
                    global_scale=global_scale_w,
                    dtype=mx.float32,
                )
                y_q = mx.qqmm(
                    x,
                    w_q,
                    scales,
                    mode=mode,
                    global_scale_x=global_scale_x,
                    global_scale_w=global_scale_w,
                )
                y_hat = x_hat @ mx.swapaxes(w_hat, -1, -2)
                self.assertEqual(y_q.shape, y_hat.shape)
                self.assertLess((y_q - y_hat).abs().max(), 1e-3)

    def test_qqmm_metal_global_scale_rejected(self):
        # Tensor-scale nvfp4 (global_scale_x / global_scale_w) is not
        # implemented in the Metal qqmm kernels. mx.qqmm must reject the
        # request on Metal rather than silently dropping the global scales
        # in the gemv path and producing incorrect results.
        if not mx.metal.is_available():
            return

        w = mx.random.normal(shape=(64, 64))
        w_q, scales = mx.quantize(w, mode="nvfp4")
        x = mx.random.normal(shape=(1, 64))
        gx = mx.array(1.0, dtype=mx.float32)
        gw = mx.array(1.0, dtype=mx.float32)

        with self.assertRaises(RuntimeError):
            y = mx.qqmm(
                x,
                w_q,
                scales,
                mode="nvfp4",
                global_scale_x=gx,
                global_scale_w=gw,
                stream=mx.gpu,
            )
            mx.eval(y)

    def test_qmm(self):
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        dtype = mx.float16 if (mx.default_device() == mx.gpu) else mx.float32
        tests = product(
            [128, 64, 32],  # group_size
            [2, 4, 8],  # bits
            [8, 32, 33, 64],  # M
            [128, 256],  # N
            [128, 256],  # K
            [True, False],  # transposed
        )
        for group_size, bits, M, N, K, transposed in tests:
            with self.subTest(
                shape=(M, N, K),
                group_size=group_size,
                bits=bits,
                transposed=transposed,
            ):
                x = mx.random.normal(shape=(M, K), key=k1) / K**0.5
                w = (
                    mx.random.normal(shape=(N, K) if transposed else (K, N), key=k2)
                    / K**0.5
                )
                x = x.astype(dtype)
                w = w.astype(dtype)
                w_q, scales, biases = mx.quantize(w, group_size, bits)
                w_hat = mx.dequantize(w_q, scales, biases, group_size, bits)
                y_q = mx.quantized_matmul(
                    x, w_q, scales, biases, transposed, group_size, bits
                )
                y_hat = (x @ w_hat.T) if transposed else (x @ w_hat)
                self.assertEqual(y_q.shape, y_hat.shape)

                tol = 1e-3 if dtype == mx.float32 else 1.5e-3
                self.assertLess((y_q - y_hat).abs().max(), tol)

    def test_qmm_large_dims(self):
        # Regression test for an int16 overflow in the NAX qmm kernels:
        # the per-simdgroup edge sizes were computed as
        # min(SN, short(N - (y_col + tn))), which wraps for distances
        # over 32767 and made store_safe skip a contiguous band of output
        # columns [N - 65536, N - 32768) whenever the M-tile was partial.
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        dtype = mx.float16 if (mx.default_device() == mx.gpu) else mx.float32
        group_size, bits = 64, 4
        K = 128
        tests = [
            (16, 32840),  # unaligned N > 2**15, M < 32: partial M-tile
            (33, 32840),  # unaligned N > 2**15, M % 32 != 0
            (33000, 64),  # M > 2**15: row distance overflows (aligned N)
        ]
        for M, N in tests:
            with self.subTest(shape=(M, N, K)):
                x = mx.random.normal(shape=(M, K), key=k1) / K**0.5
                w = mx.random.normal(shape=(N, K), key=k2) / K**0.5
                x = x.astype(dtype)
                w = w.astype(dtype)
                w_q, scales, biases = mx.quantize(w, group_size, bits)
                w_hat = mx.dequantize(w_q, scales, biases, group_size, bits)
                y_q = mx.quantized_matmul(
                    x, w_q, scales, biases, True, group_size, bits
                )
                y_hat = x @ w_hat.T
                self.assertEqual(y_q.shape, y_hat.shape)
                tol = 1e-3 if dtype == mx.float32 else 1.5e-3
                self.assertLess((y_q - y_hat).abs().max(), tol)

    def test_qmm_vjp(self):
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)

        bits = 8
        group_size = 64
        M = 64
        N = 1024
        K = 512

        x = mx.random.normal(shape=(2, M, K), key=k1)
        c = mx.ones(shape=(2, M, N))

        transposes = [True, False]
        for transposed in transposes:
            w = mx.random.normal(shape=(N, K) if transposed else (K, N), key=k2)
            w_q, scales, biases = mx.quantize(w, group_size, bits)

            def fn(x):
                return mx.quantized_matmul(
                    x, w_q, scales, biases, transposed, group_size, bits
                )

            _, vjp_out = mx.vjp(fn, primals=(x,), cotangents=(c,))

            expected_out = mx.quantized_matmul(
                c, w_q, scales, biases, not transposed, group_size, bits
            )
            self.assertTrue(mx.allclose(vjp_out[0], expected_out))

    def test_qmm_jvp(self):
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)

        bits = 8
        group_size = 64
        M = 64
        N = 128
        K = 128

        x = mx.random.normal(shape=(2, M, K), key=k1)
        x_tan = mx.ones(shape=(2, M, N))

        transposes = [True, False]
        for transposed in transposes:
            w = mx.random.normal(shape=(N, K) if transposed else (K, N), key=k2)
            w_q, scales, biases = mx.quantize(w, group_size, bits)

            def fn(x):
                return mx.quantized_matmul(
                    x, w_q, scales, biases, transposed, group_size, bits
                )

            _, jvp_out = mx.jvp(fn, primals=(x,), tangents=(x_tan,))

            expected_out = mx.quantized_matmul(
                x_tan, w_q, scales, biases, transposed, group_size, bits
            )
            self.assertTrue(mx.allclose(jvp_out[0], expected_out))

    def test_qmm_shapes(self):
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        group_size = 64
        bits = 4
        w = mx.random.normal(shape=(32, 256), key=k2)
        w_q, scales, biases = mx.quantize(w, group_size, bits)
        w_hat = mx.dequantize(w_q, scales, biases, group_size, bits)
        for s in [(3, 256), (2, 1, 7, 256)]:
            x = mx.random.normal(shape=s, key=k1)
            y_q = mx.quantized_matmul(x, w_q, scales, biases, True, group_size, bits)
            y_hat = x @ w_hat.T
            self.assertEqual(y_q.shape, y_hat.shape)
            self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        w = mx.random.normal(shape=(256, 256), key=k2)
        w_q, scales, biases = mx.quantize(w, group_size, bits)
        w_hat = mx.dequantize(w_q, scales, biases, group_size, bits)
        for s in [(3, 256), (2, 1, 7, 256)]:
            x = mx.random.normal(shape=s, key=k1)
            y_q = mx.quantized_matmul(x, w_q, scales, biases, False, group_size, bits)
            y_hat = x @ w_hat
            self.assertEqual(y_q.shape, y_hat.shape)
            self.assertLess((y_q - y_hat).abs().max(), 1e-3)

    def test_qmv(self):
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        tests = product(
            [128, 64, 32],  # group_size
            [2, 3, 4, 5, 6, 8],  # bits
            [256, 512, 67],  # M
            [64, 256],  # N
            [0, 1, 3, 8],  # B
        )
        for group_size, bits, M, N, B in tests:
            if group_size > N:
                continue
            with self.subTest(shape=(B, M, N), group_size=group_size, bits=bits):
                x_shape = (3, 1, N) if B == 0 else (B, 1, N)
                w_shape = (M, N) if B == 0 else (B, M, N)
                x = mx.random.normal(shape=x_shape, key=k1) / N**0.5
                w = mx.random.normal(shape=w_shape, key=k2) / N**0.5
                w_q, scales, biases = mx.quantize(w, group_size, bits)
                w_hat = mx.dequantize(w_q, scales, biases, group_size, bits)
                y_q = mx.quantized_matmul(
                    x, w_q, scales, biases, True, group_size, bits
                )
                y_hat = x @ mx.swapaxes(w_hat, -1, -2)
                self.assertEqual(y_q.shape, y_hat.shape)
                self.assertLess((y_q - y_hat).abs().max(), 1e-3)

    def test_fp_qmv(self):
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        tests = product(
            [256, 512, 67, 5, 7],  # M -- 5, 7 exercise out_vec_size < 8 (#3762)
            [64, 256],  # N
            [0, 1, 3, 8],  # B
        )
        modes = ["mxfp4", "nvfp4", "mxfp8"]
        for M, N, B in tests:
            for mode in modes:
                with self.subTest(shape=(B, M, N), mode=mode):
                    x_shape = (3, 1, N) if B == 0 else (B, 1, N)
                    w_shape = (M, N) if B == 0 else (B, M, N)
                    x = mx.random.normal(shape=x_shape, key=k1)
                    w = mx.random.normal(shape=w_shape, key=k2)
                    w_q, scales = mx.quantize(w, mode=mode)
                    w_hat = mx.dequantize(w_q, scales, mode=mode)
                    y_q = mx.quantized_matmul(
                        x,
                        w_q,
                        scales,
                        transpose=True,
                        mode=mode,
                    )
                    y_hat = x @ mx.swapaxes(w_hat, -1, -2)
                    self.assertEqual(y_q.shape, y_hat.shape)
                    self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        # Test multiple of 16 but not 32
        M = 128
        N = 48
        mode = "nvfp4"
        with self.subTest(shape=(B, M, N), mode=mode):
            x_shape = (1, N)
            w_shape = (M, N)
            x = mx.random.normal(shape=x_shape, key=k1)
            w = mx.random.normal(shape=w_shape, key=k2)
            w_q, scales = mx.quantize(w, mode=mode)
            w_hat = mx.dequantize(w_q, scales, mode=mode)
            y_q = mx.quantized_matmul(
                x,
                w_q,
                scales,
                transpose=True,
                mode=mode,
            )
            y_hat = x @ mx.swapaxes(w_hat, -1, -2)
            self.assertEqual(y_q.shape, y_hat.shape)
            self.assertLess((y_q - y_hat).abs().max(), 1e-3)

    def test_qmv_wide(self):
        # M in [2, vector_limit) routes to qmv_wide -- except K in {64, 128}
        # with power-of-2 bits, which stays on qmv_quad. Check both paths
        # against a dequantize-then-matmul reference, with ragged M (token
        # tail) and ragged N (output-tile remainder). B > 1 stacks a distinct
        # weight matrix per slab and exercises the batched variant.
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        # M <= 9 < vector_limit for these shapes (K, N <= 2048), so all stay on
        # the mat-vec path; 7 and 9 also exercise the token-tail guard.
        Ms = [2, 3, 4, 5, 6, 7, 9]
        Ns = [256, 67]  # 67 is a non-multiple of the 4-row output tile
        Bs = [1, 3]

        # Affine: every bit-width and group size.
        for group_size, bits, K in product(
            [32, 64, 128], [2, 3, 4, 5, 6, 8], [128, 512]
        ):
            for M, N, B in product(Ms, Ns, Bs):
                with self.subTest(M=M, N=N, K=K, B=B, group_size=group_size, bits=bits):
                    x_shape = (M, K) if B == 1 else (B, M, K)
                    w_shape = (N, K) if B == 1 else (B, N, K)
                    x = mx.random.normal(shape=x_shape, key=k1)
                    w = mx.random.normal(shape=w_shape, key=k2)
                    w_q, scales, biases = mx.quantize(w, group_size, bits)
                    w_hat = mx.dequantize(w_q, scales, biases, group_size, bits)
                    y_q = mx.quantized_matmul(
                        x, w_q, scales, biases, True, group_size, bits
                    )
                    y_hat = x @ mx.swapaxes(w_hat, -1, -2)
                    self.assertEqual(y_q.shape, y_hat.shape)
                    self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        # FP modes (group_size and bits implied by the mode).
        for mode, K in product(["mxfp4", "nvfp4", "mxfp8"], [128, 512]):
            for M, N, B in product(Ms, Ns, Bs):
                with self.subTest(M=M, N=N, K=K, B=B, mode=mode):
                    x_shape = (M, K) if B == 1 else (B, M, K)
                    w_shape = (N, K) if B == 1 else (B, N, K)
                    x = mx.random.normal(shape=x_shape, key=k1)
                    w = mx.random.normal(shape=w_shape, key=k2)
                    w_q, scales = mx.quantize(w, mode=mode)
                    w_hat = mx.dequantize(w_q, scales, mode=mode)
                    y_q = mx.quantized_matmul(x, w_q, scales, transpose=True, mode=mode)
                    y_hat = x @ mx.swapaxes(w_hat, -1, -2)
                    self.assertEqual(y_q.shape, y_hat.shape)
                    self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        # Tiny shapes (M, K, N): small K and non-multiple output rows.
        tiny = [(2, 32, 10), (4, 32, 7), (3, 64, 5), (5, 64, 3)]
        settings = [(4, 32, "affine"), (6, 32, "affine"), (4, 16, "nvfp4")]
        for M, K, N in tiny:
            for bits, group_size, mode in settings:
                with self.subTest(
                    M=M, K=K, N=N, bits=bits, group_size=group_size, mode=mode
                ):
                    x = mx.random.normal(shape=(M, K), key=k1)
                    w = mx.random.normal(shape=(N, K), key=k2)
                    w_q, *sb = mx.quantize(
                        w, group_size=group_size, bits=bits, mode=mode
                    )
                    w_hat = mx.dequantize(
                        w_q, *sb, group_size=group_size, bits=bits, mode=mode
                    )
                    y_q = mx.quantized_matmul(
                        x,
                        w_q,
                        *sb,
                        transpose=True,
                        group_size=group_size,
                        bits=bits,
                        mode=mode,
                    )
                    y_hat = x @ mx.swapaxes(w_hat, -1, -2)
                    self.assertEqual(y_q.shape, y_hat.shape)
                    self.assertLess((y_q - y_hat).abs().max(), 1e-3)

    def test_qvm(self):
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        tests = product(
            [128, 64, 32],  # group_size
            [2, 3, 4, 5, 6, 8],  # bits
            [32, 128, 256],  # M
            [128, 256, 67],  # N
            [0, 1, 3, 8],  # B
        )
        for group_size, bits, M, N, B in tests:
            with self.subTest(shape=(B, M, N), group_size=group_size, bits=bits):
                if M < group_size:
                    continue
                x_shape = (1, N) if B == 0 else (B, 1, N)
                w_shape = (N, M) if B == 0 else (B, N, M)
                x = mx.random.normal(shape=x_shape, key=k1)
                w = mx.random.normal(shape=w_shape, key=k2)
                w_q, scales, biases = mx.quantize(w, group_size, bits)
                w_hat = mx.dequantize(w_q, scales, biases, group_size, bits)
                y_q = mx.quantized_matmul(
                    x, w_q, scales, biases, False, group_size, bits
                )
                y_hat = x @ w_hat
                self.assertEqual(y_q.shape, y_hat.shape)
                self.assertLess((y_q - y_hat).abs().max(), 1e-3)

    def test_qvm_splitk(self):
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        tests = product(
            [128, 64, 32],  # group_size
            [2, 4, 8],  # bits
            [128],  # M
            [16384],  # N
            [1, 3],  # B
        )
        for group_size, bits, M, N, B in tests:
            with self.subTest(shape=(B, M, N), group_size=group_size, bits=bits):
                x_shape = (1, N) if B == 0 else (B, 1, N)
                w_shape = (N, M) if B == 0 else (B, N, M)
                x = 1e-1 * mx.random.normal(shape=x_shape, key=k1)
                w = 1e-1 * mx.random.normal(shape=w_shape, key=k2)
                w_q, scales, biases = mx.quantize(w, group_size, bits)
                w_hat = mx.dequantize(w_q, scales, biases, group_size, bits)
                y_q = mx.quantized_matmul(
                    x, w_q, scales, biases, False, group_size, bits
                )
                y_hat = x @ w_hat
                self.assertEqual(y_q.shape, y_hat.shape)
                self.assertLess((y_q - y_hat).abs().max(), 2e-3)

        # Test with 1D vector
        group_size = 32
        bits = 8
        N = 2048
        x = 1e-1 * mx.random.normal(shape=(N,), key=k1)
        w = 1e-1 * mx.random.normal(shape=(N, N), key=k2)
        w_q, scales, biases = mx.quantize(w, group_size, bits)
        w_hat = mx.dequantize(w_q, scales, biases, group_size, bits)
        y_q = mx.quantized_matmul(x, w_q, scales, biases, False, group_size, bits)
        y_hat = x @ w_hat
        self.assertEqual(y_q.shape, y_hat.shape)
        self.assertLess((y_q - y_hat).abs().max(), 2e-3)

    def test_qvm_splitk_multi_row(self):
        # Test qvm split_k with M > 1 to ensure the x row stride is correct
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        tests = product(
            [64, 32],  # group_size
            [4, 8],  # bits
            [128],  # out dim (N)
            [2048, 4096],  # in dim (K) >= 1024 to trigger split_k
            [2, 3],  # M (multiple rows)
        )
        for group_size, bits, N, K, M in tests:
            with self.subTest(M=M, K=K, N=N, group_size=group_size, bits=bits):
                x = 1e-1 * mx.random.normal(shape=(M, K), key=k1)
                w = 1e-1 * mx.random.normal(shape=(K, N), key=k2)
                w_q, scales, biases = mx.quantize(w, group_size, bits)
                w_hat = mx.dequantize(w_q, scales, biases, group_size, bits)
                y_q = mx.quantized_matmul(
                    x, w_q, scales, biases, False, group_size, bits
                )
                y_hat = x @ w_hat
                self.assertEqual(y_q.shape, y_hat.shape)
                self.assertLess((y_q - y_hat).abs().max(), 2e-3)

    def test_fp_qvm(self):
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        tests = product(
            [32, 128, 256],  # M
            [128, 256, 67],  # N
            [0, 1, 3, 8],  # B
        )
        # Add a splitk
        tests = list(tests)
        tests.append((128, 16384, 0))
        modes = ["mxfp4", "nvfp4", "mxfp8"]

        for M, N, B in tests:
            for mode in modes:
                with self.subTest(shape=(B, M, N), mode=mode):
                    x_shape = (1, N) if B == 0 else (B, 1, N)
                    w_shape = (N, M) if B == 0 else (B, N, M)
                    x = mx.random.normal(shape=x_shape, key=k1)
                    w = mx.random.normal(shape=w_shape, key=k2)
                    w_q, scales = mx.quantize(w, mode=mode)
                    w_hat = mx.dequantize(w_q, scales, mode=mode)
                    y_q = mx.quantized_matmul(
                        x,
                        w_q,
                        scales,
                        transpose=False,
                        mode=mode,
                    )
                    y_hat = x @ w_hat
                    self.assertEqual(y_q.shape, y_hat.shape)
                    self.assertLess((y_q - y_hat).abs().max(), 2e-3)

    def test_mode_error_cases(self):
        w = mx.random.normal(shape=(256, 256))
        x = mx.random.normal(shape=(1, 256))

        # Invalid mode
        with self.assertRaises(ValueError):
            mx.quantize(w, mode="xyz")

        wq, scales, biases = mx.quantize(w, bits=4, group_size=32)

        with self.assertRaises(ValueError):
            mx.dequantize(wq, scales, biases, bits=4, group_size=32, mode="xyz")

        with self.assertRaises(ValueError):
            mx.quantized_matmul(
                x, wq, scales, biases, bits=4, group_size=32, mode="xyz"
            )

        rhs_indices = mx.array(0)
        with self.assertRaises(ValueError):
            mx.gather_qmm(
                x,
                wq,
                scales,
                biases,
                rhs_indices=rhs_indices,
                bits=4,
                group_size=32,
                mode="xyz",
            )

        # Only quantize floating point types
        with self.assertRaises(ValueError):
            mx.quantize(mx.zeros((128, 128), mx.int32))

        with self.assertRaises(ValueError):
            mx.quantize(mx.zeros((128, 128), mx.int32), mode="mxfp4")

        # Must have bias for affine
        with self.assertRaises(ValueError):
            mx.dequantize(wq, scales, None, bits=4, group_size=32)

        with self.assertRaises(ValueError):
            mx.quantized_matmul(x, wq, scales, None, bits=4, group_size=32)

        with self.assertRaises(ValueError):
            mx.gather_qmm(
                x, wq, scales, None, rhs_indices=rhs_indices, bits=4, group_size=32
            )

        # Must be floating point
        x = mx.zeros(shape=(256,), dtype=mx.int32)
        scales = mx.zeros(scales.shape, dtype=mx.int32)
        biases = mx.zeros(scales.shape, dtype=mx.int32)
        with self.assertRaises(ValueError):
            mx.dequantize(wq, scales, biases, bits=4, group_size=32)

        with self.assertRaises(ValueError):
            mx.quantized_matmul(x, wq, scales, biases, bits=4, group_size=32)

        with self.assertRaises(ValueError):
            mx.gather_qmm(
                x, wq, scales, biases, rhs_indices=rhs_indices, bits=4, group_size=32
            )

    def test_throw(self):
        x = mx.random.normal(shape=(10, 512))
        w = mx.random.normal(shape=(32, 512))
        w_q, scales, biases = mx.quantize(w)

        with self.assertRaises(ValueError):
            mx.quantized_matmul(x, w_q.T, scales, biases)
        with self.assertRaises(ValueError):
            mx.quantized_matmul(x, w_q.T, scales.T, biases)
        with self.assertRaises(ValueError):
            mx.quantized_matmul(x, w_q, scales, biases, False)
        with self.assertRaises(ValueError):
            mx.quantized_matmul(x, w_q, scales.T, biases.T)
        y = mx.quantized_matmul(x, w_q, scales, biases, True)
        mx.eval(y)

    def test_small_matrix(self):
        for w_shape in [(8, 256), (1, 8, 256), (3, 8, 256)]:
            with self.subTest(w_shape=w_shape):
                w = mx.random.normal(shape=(w_shape))
                w_q, scales, biases = mx.quantize(w)
                w_hat = mx.dequantize(w_q, scales, biases)

                # Test qmv
                for shape in [(3, 1, 256), (3, 4, 256)]:
                    x = mx.random.normal(shape=shape)
                    y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=True)
                    y_hat = x @ mx.swapaxes(w_hat, -1, -2)
                    self.assertEqual(y_q.shape, y_hat.shape)
                    self.assertLess((y_q - y_hat).abs().max(), 1e-3)

                # Test qmm_t
                x = mx.random.normal(shape=(3, 10, 256))
                y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=True)
                y_hat = x @ mx.swapaxes(w_hat, -1, -2)
                self.assertEqual(y_q.shape, y_hat.shape)
                self.assertLess((y_q - y_hat).abs().max(), 1e-3)

                # Test qvm
                x = mx.random.normal(shape=(3, 1, 8))
                y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=False)
                y_hat = x @ w_hat
                self.assertEqual(y_q.shape, y_hat.shape)
                self.assertLess((y_q - y_hat).abs().max(), 1e-3)

                # Test qmm
                x = mx.random.normal(shape=(3, 10, 8))
                y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=False)
                y_hat = x @ w_hat
                self.assertEqual(y_q.shape, y_hat.shape)
                self.assertLess((y_q - y_hat).abs().max(), 1e-3)

    def test_non_multiples(self):
        w = mx.random.normal(shape=(33, 256))
        w_q, scales, biases = mx.quantize(w)
        w_hat = mx.dequantize(w_q, scales, biases)

        # Test qmv
        x = mx.random.normal(shape=(1, 256))
        y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=True)
        y_hat = x @ w_hat.T
        self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        # Test qmm_t
        x = mx.random.normal(shape=(10, 256))
        y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=True)
        y_hat = x @ w_hat.T
        self.assertEqual(y_q.shape, y_hat.shape)
        self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        # Test qvm
        x = mx.random.normal(shape=(1, 33))
        y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=False)
        y_hat = x @ w_hat
        self.assertEqual(y_q.shape, y_hat.shape)
        self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        # Test qmm
        x = mx.random.normal(shape=(10, 33))
        y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=False)
        y_hat = x @ w_hat
        self.assertEqual(y_q.shape, y_hat.shape)
        self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        # Smaller than 8
        w = mx.random.normal(shape=(3, 256))
        w_q, scales, biases = mx.quantize(w)
        w_hat = mx.dequantize(w_q, scales, biases)

        # Test qmv
        x = mx.random.normal(shape=(1, 256))
        y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=True)
        y_hat = x @ w_hat.T
        self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        # Test qmm_t
        x = mx.random.normal(shape=(10, 256))
        y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=True)
        y_hat = x @ w_hat.T
        self.assertEqual(y_q.shape, y_hat.shape)
        self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        # Test qvm
        x = mx.random.normal(shape=(1, 3))
        y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=False)
        y_hat = x @ w_hat
        self.assertEqual(y_q.shape, y_hat.shape)
        self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        # Test qmm
        x = mx.random.normal(shape=(10, 3))
        y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=False)
        y_hat = x @ w_hat
        self.assertEqual(y_q.shape, y_hat.shape)
        self.assertLess((y_q - y_hat).abs().max(), 1e-3)

        # Test with larger than 128 unaligned sizes
        w = mx.random.normal(shape=(99, 256))
        w_q, scales, biases = mx.quantize(w)
        w_hat = mx.dequantize(w_q, scales, biases)
        x = mx.random.normal(shape=(129, 256))
        y_q = mx.quantized_matmul(x, w_q, scales, biases, transpose=True)
        y_hat = x @ w_hat.T
        self.assertEqual(y_q.shape, y_hat.shape)
        self.assertLess((y_q - y_hat).abs().max(), 1e-3)

    def test_qmv_small_non_multiples(self):
        # Test very small K and N dimensions (e.g., [MxK] x [NxK].T = [MxN])
        # Each tuple is (M, K, N) representing input rows, weight cols, weight rows
        test_cases = [
            (1, 32, 3),
            (2, 32, 10),
            (1, 32, 5),
            (4, 32, 7),
        ]

        # Test different quantization settings (bits, group_size, mode)
        quantization_settings = [
            (4, 32, "affine"),
            (6, 32, "affine"),
            (4, 16, "nvfp4"),
        ]

        for M, K, N in test_cases:
            for bits, group_size, mode in quantization_settings:
                # Test without batch dimension
                with self.subTest(
                    M=M,
                    K=K,
                    N=N,
                    batch=None,
                    group_size=group_size,
                    bits=bits,
                    mode=mode,
                ):
                    w = mx.random.normal(shape=(N, K))
                    w_q, *sb = mx.quantize(
                        w,
                        group_size=group_size,
                        bits=bits,
                        mode=mode,
                    )
                    w_hat = mx.dequantize(
                        w_q,
                        *sb,
                        group_size=group_size,
                        bits=bits,
                        mode=mode,
                    )

                    # Test qmv/qmm_t (transpose=True): [MxK] @ [NxK].T = [MxN]
                    x = mx.random.normal(shape=(M, K))
                    y_q = mx.quantized_matmul(
                        x,
                        w_q,
                        *sb,
                        transpose=True,
                        group_size=group_size,
                        bits=bits,
                        mode=mode,
                    )
                    y_hat = x @ mx.swapaxes(w_hat, -1, -2)
                    self.assertEqual(y_q.shape, y_hat.shape)
                    self.assertLess((y_q - y_hat).abs().max(), 1e-3)

    def test_gather_qmm(self):
        def quantize(w, transpose=True, group_size=None, bits=None, mode="affine"):
            if mode == "affine":
                qw, s, b = mx.quantize(w, group_size=group_size, bits=bits, mode=mode)
            else:
                qw, s = mx.quantize(w, group_size=group_size, bits=bits, mode=mode)
                b = None
            w_hat = mx.dequantize(qw, s, b, group_size=group_size, bits=bits, mode=mode)
            if transpose:
                w_hat = w_hat.swapaxes(-1, -2)
            return w_hat, qw, s, b

        def test_shape(
            M,
            N,
            K,
            dtype=mx.float32,
            batch_A=(),
            batch_B=(),
            lhs_indices=None,
            rhs_indices=None,
            transpose=True,
            group_size=None,
            bits=None,
            mode="affine",
        ):
            with self.subTest(
                M=M,
                N=N,
                K=K,
                dtype=dtype,
                batch_A=batch_A,
                batch_B=batch_B,
                lhs_indices=lhs_indices,
                rhs_indices=rhs_indices,
                transpose=transpose,
                group_size=group_size,
                bits=bits,
                mode=mode,
            ):
                x = mx.random.normal(shape=batch_A + (M, K)).astype(dtype)
                w = mx.random.normal(
                    shape=batch_B + ((N, K) if transpose else (K, N))
                ).astype(dtype)
                w_hat, qw, s, b = quantize(w, transpose, group_size, bits, mode=mode)

                if lhs_indices is not None:
                    lhs_indices = mx.array(lhs_indices)
                if rhs_indices is not None:
                    rhs_indices = mx.array(rhs_indices)

                c1 = mx.gather_mm(x, w_hat, lhs_indices, rhs_indices)
                c2 = mx.gather_qmm(
                    x,
                    qw,
                    s,
                    b,
                    lhs_indices,
                    rhs_indices,
                    transpose=transpose,
                    group_size=group_size,
                    bits=bits,
                    mode=mode,
                )
                self.assertTrue(mx.allclose(c1, c2, atol=1e-4))

        inputs = (
            {
                "batch_A": (1,),
                "lhs_indices": (0,),
                "batch_B": (3,),
                "rhs_indices": (2, 1),
            },
            {
                "batch_A": (1,),
                "lhs_indices": None,
                "batch_B": (3,),
                "rhs_indices": (2, 1),
            },
            {
                "batch_A": (2,),
                "lhs_indices": None,
                "batch_B": (3,),
                "rhs_indices": (2, 1),
            },
            {
                "batch_A": (3,),
                "lhs_indices": (0, 2),
                "batch_B": (1,),
                "rhs_indices": (0,),
            },
            {
                "batch_A": (5,),
                "lhs_indices": (0, 2),
                "batch_B": (3,),
                "rhs_indices": (2, 1),
            },
            {
                "batch_A": (4, 2),
                "lhs_indices": (
                    (7, 6),
                    (5, 4),
                    (1, 2),
                ),
                "batch_B": (4, 1),
                "rhs_indices": ((2,), (0,), (1,)),
            },
            {
                "batch_A": (1,),
                "lhs_indices": (0,),
                "batch_B": (3,),
                "rhs_indices": (2, 1),
                "mode": "nvfp4",
            },
            {
                "batch_A": (1,),
                "lhs_indices": (0,),
                "batch_B": (3,),
                "rhs_indices": (2, 1),
                "mode": "mxfp4",
            },
            {
                "batch_A": (1,),
                "lhs_indices": (0,),
                "batch_B": (3,),
                "rhs_indices": (2, 1),
                "mode": "mxfp8",
            },
            {
                "batch_A": (1,),
                "lhs_indices": (0,),
                "batch_B": (3,),
                "rhs_indices": (2, 1),
                "mode": "ternary",
            },
        )

        for kwargs in inputs:
            test_shape(1, 32, 128, **kwargs)
            test_shape(32, 32, 256, **kwargs)
            test_shape(1, 32, 256, **kwargs)
            test_shape(32, 256, 32, transpose=False, **kwargs)
            test_shape(1, 256, 32, transpose=False, **kwargs)
            test_shape(32, 32, 512, **kwargs)
            test_shape(1, 32, 512, **kwargs)
            test_shape(32, 512, 32, transpose=False, **kwargs)
            test_shape(1, 512, 32, transpose=False, **kwargs)

    def test_qmm_fp_type(self):
        indices = mx.array([[2], [0], [1]], dtype=mx.uint32)

        modes = ["mxfp8", "mxfp4"]
        for mode in modes:
            for t in [mx.bfloat16, mx.float16, mx.float32]:
                x = mx.random.normal((32, 256)).astype(t)

                w = mx.random.normal((32, 256))
                wq, s = mx.quantize(w, mode=mode)
                out = mx.quantized_matmul(x, wq, s, mode=mode)
                self.assertEqual(out.dtype, t)

                w = mx.random.normal((4, 32, 256))
                wq, s = mx.quantize(w, mode=mode)

                out = mx.gather_qmm(x, wq, s, rhs_indices=indices, mode=mode)
                self.assertEqual(out.dtype, t)

    def test_gather_matmul_grad(self):
        def quantize(w, transpose=True, group_size=64, bits=4):
            qw, s, b = mx.quantize(w, group_size=group_size, bits=bits)
            w_hat = mx.dequantize(qw, s, b, group_size=group_size, bits=bits)
            if transpose:
                w_hat = w_hat.swapaxes(-1, -2)
            return w_hat, qw, s, b

        lhs_indices = mx.array([[7, 6], [4, 1], [0, 2]], dtype=mx.uint32)
        rhs_indices = mx.array([[2], [0], [1]], dtype=mx.uint32)

        x = mx.random.normal((4, 2, 32, 256))
        w = mx.random.normal((4, 1, 32, 256))
        w_hat, qw, s, b = quantize(w)

        def f_ref(x, w, i1, i2):
            return mx.gather_mm(x, w, i1, i2).sum()

        def f_test(x, qw, s, b, i1, i2):
            return mx.gather_qmm(x, qw, s, b, i1, i2, transpose=True).sum()

        r1 = f_ref(x, w_hat, lhs_indices, rhs_indices)
        r2 = f_test(x, qw, s, b, lhs_indices, rhs_indices)
        self.assertTrue(mx.allclose(r1, r2, atol=1e-4))

        g1 = mx.grad(f_ref)(x, w_hat, lhs_indices, rhs_indices)
        g2 = mx.grad(f_test)(x, qw, s, b, lhs_indices, rhs_indices)
        self.assertTrue(mx.allclose(g1, g2, atol=1e-4))

    def test_gather_qmm_matrix_path(self):
        # Regression test for matrix-size gather_qmm with half precision
        # inputs: on NAX devices the kernel name was built with bk = 32
        # while the kernels are only instantiated with bk = 64, so the
        # kernel lookup failed with "Unable to load kernel".
        key = mx.random.key(0)
        k1, k2 = mx.random.split(key)
        dtype = mx.bfloat16 if (mx.default_device() == mx.gpu) else mx.float32
        E, M, N, K = 4, 64, 512, 512
        lhs_indices = mx.array([0, 1, 2], dtype=mx.uint32)
        rhs_indices = mx.array([0, 2, 3], dtype=mx.uint32)
        for mode in ["affine", "mxfp4"]:
            with self.subTest(mode=mode):
                x = (mx.random.normal(shape=(3, M, K), key=k1) / K**0.5).astype(dtype)
                # Keep w in the same dtype so affine scales do not promote
                # the matmul to float32 (which would skip the NAX route).
                w = mx.random.normal(shape=(E, N, K), key=k2).astype(dtype)
                w_q, *wargs = mx.quantize(w, mode=mode)
                w_hat = mx.dequantize(w_q, *wargs, mode=mode)
                y_q = mx.gather_qmm(
                    x,
                    w_q,
                    *wargs,
                    lhs_indices=lhs_indices,
                    rhs_indices=rhs_indices,
                    transpose=True,
                    mode=mode,
                )
                y_hat = mx.stack(
                    [
                        x[i].astype(mx.float32) @ w_hat[int(rhs_indices[i])].T
                        for i in range(3)
                    ]
                ).astype(dtype)
                self.assertEqual(y_q.shape, y_hat.shape)
                self.assertLess((y_q - y_hat).abs().max(), 1e-1)

    def test_gather_qmm_sorted(self):
        def quantize(w, transpose=True, group_size=None, mode="affine"):
            if mode == "affine":
                qw, s, b = mx.quantize(w, group_size=group_size, mode=mode)
            else:
                qw, s = mx.quantize(w, mode=mode)
                b = None

            w_hat = mx.dequantize(qw, s, b, group_size=group_size, mode=mode)
            if transpose:
                w_hat = w_hat.swapaxes(-1, -2)
            return w_hat, qw, s, b

        def gather_sort(x, indices):
            N, M = indices.shape
            indices = indices.flatten()
            order = mx.argsort(indices)
            inv_order = mx.argsort(order)
            return x.flatten(0, -3)[order // M], indices[order], inv_order

        def scatter_unsort(x, inv_order, shape=None):
            x = x[inv_order]
            if shape is not None:
                x = mx.unflatten(x, 0, shape)
            return x

        parameters = [
            # L, K, D, E, I, transpose
            (32, 512, 512, 4, 2, True, "affine"),
            (32, 512, 544, 4, 2, True, "mxfp4"),
            (32, 512, 544, 4, 2, True, "nvfp4"),
            (32, 512, 544, 4, 2, True, "mxfp8"),
            (133, 512, 512, 4, 2, True, "affine"),
            (133, 512, 555, 4, 2, True, "affine"),
            (133, 512, 512, 4, 2, True, "affine"),
            (64, 512, 512, 4, 2, False, "affine"),
            (64, 512, 544, 4, 2, False, "mxfp4"),
            (64, 512, 544, 4, 2, False, "nvfp4"),
            (64, 512, 544, 4, 2, False, "mxfp8"),
            (133, 512, 512, 4, 2, False, "affine"),
            (133, 512, 544, 4, 2, False, "affine"),
            (133, 512, 555, 4, 2, False, "affine"),
            (64, 512, 512, 4, 2, False, "affine"),
        ]

        key = mx.random.key(0)
        k1, k2, k3 = mx.random.split(key, 3)
        dtype = mx.float16 if (mx.default_device() == mx.gpu) else mx.float32

        for L, K, D, E, I, transpose, mode in parameters:
            with self.subTest(L=L, K=K, D=D, E=E, I=I, transpose=transpose, mode=mode):
                if mode != "affine":
                    group_size = None
                    dtype = (
                        mx.bfloat16 if (mx.default_device() == mx.gpu) else mx.float32
                    )
                else:
                    group_size = 64
                    dtype = (
                        mx.float16 if (mx.default_device() == mx.gpu) else mx.float32
                    )

                K, D = (K, D) if transpose else (D, K)
                ishape = (L, I)
                xshape = (L, 1, 1, K)
                wshape = (E, D, K) if transpose else (E, K, D)

                indices = (mx.random.uniform(shape=ishape, key=k1) * E).astype(
                    mx.uint32
                )
                x = mx.random.normal(xshape, key=k2) / K**0.5
                w = mx.random.normal(wshape, key=k3) / K**0.5

                x = x.astype(dtype)
                w = w.astype(dtype)

                w, *wq = quantize(
                    w, group_size=group_size, mode=mode, transpose=transpose
                )

                y1 = mx.gather_mm(x, w, rhs_indices=indices)
                y2 = mx.gather_qmm(
                    x,
                    *wq,
                    group_size=group_size,
                    mode=mode,
                    transpose=transpose,
                    rhs_indices=indices,
                )
                xs, idx, inv_order = gather_sort(x, indices)
                y3 = mx.gather_mm(xs, w, rhs_indices=idx, sorted_indices=True)

                y4 = mx.gather_qmm(
                    xs,
                    *wq,
                    group_size=group_size,
                    mode=mode,
                    rhs_indices=idx,
                    transpose=transpose,
                    sorted_indices=True,
                )
                y3 = scatter_unsort(y3, inv_order, indices.shape)
                y4 = scatter_unsort(y4, inv_order, indices.shape)

                tol = 1.5e-5 if (dtype == mx.float32) else 1e-3

                self.assertLess((y1 - y2).abs().max(), tol)
                self.assertLess((y1 - y3).abs().max(), tol)
                self.assertLess((y1 - y4).abs().max(), tol)

                self.assertTrue(mx.allclose(y1, y2, atol=tol))
                self.assertTrue(mx.allclose(y1, y3, atol=tol))
                self.assertTrue(mx.allclose(y1, y4, atol=tol))

    def test_gather_qmm_grad(self):
        def gather_qmm_ref(x, w, s, b, lhs, rhs, trans, sort):
            if lhs is not None:
                x = x[lhs]
            if rhs is not None:
                w = w[rhs]
                s = s[rhs]
                b = b[rhs]
            return mx.quantized_matmul(x, w, s, b, transpose=trans)

        def gather_qmm(x, w, s, b, lhs, rhs, trans, sort):
            return mx.gather_qmm(
                x,
                w,
                s,
                b,
                transpose=trans,
                lhs_indices=lhs,
                rhs_indices=rhs,
                sorted_indices=sort,
            )

        key = mx.random.key(0)
        k1, k2, k3, k4 = mx.random.split(key, 4)
        dtype = mx.float32

        x = mx.random.normal((16, 1, 256), key=k1).astype(dtype)
        w, s, b = mx.quantize(mx.random.normal((4, 256, 256), key=k2).astype(dtype))
        indices = mx.sort(mx.random.randint(0, 4, shape=(16,), key=k3))
        cotan = mx.random.normal((16, 1, 256), key=k4).astype(dtype)

        (o1,), (dx1, ds1, db1) = mx.vjp(
            lambda x, s, b: gather_qmm_ref(x, w, s, b, None, indices, True, True),
            [x, s, b],
            [cotan],
        )
        (o2,), (dx2, ds2, db2) = mx.vjp(
            lambda x, s, b: gather_qmm(x, w, s, b, None, indices, True, True),
            [x, s, b],
            [cotan],
        )

        self.assertLess((o1 - o2).abs().max(), 1e-4)
        self.assertTrue(mx.allclose(o1, o2, atol=1e-4))
        self.assertTrue(mx.allclose(dx1, dx2, atol=1e-4))
        self.assertTrue(mx.allclose(ds1, ds2, atol=1e-3))
        self.assertTrue(mx.allclose(db1, db2, atol=1e-3))

    def test_vjp_scales_biases(self):
        mx.random.seed(0)
        x = mx.random.normal(shape=(2, 2, 512))
        w = mx.random.normal(shape=(512, 512))
        wq, s, b = mx.quantize(w, bits=4, group_size=64)

        def mm(sb, x, wq):
            return mx.quantized_matmul(x, wq, *sb, bits=4, group_size=64).sum()

        params = (s, b)
        dparams = mx.grad(mm)((s, b), x, wq)

        eps = 8e-3
        # numerical grad check with a few indices
        indices = [(0, 0), (11, 4), (22, 7)]
        for idx in indices:
            for p in [0, 1]:
                params[p][idx] += eps
                out_up = mm(params, x, wq)
                params[p][idx] -= 2 * eps
                out_down = mm(params, x, wq)
                params[p][idx] += eps
                num_ds = (out_up - out_down) / (2 * eps)
                self.assertAlmostEqual(dparams[p][idx], num_ds, delta=2e-2)

    def test_fp_vjp_scales_throws(self):
        mx.random.seed(0)
        x = mx.random.normal(shape=(2, 512))
        w = mx.random.normal(shape=(512, 512))
        for mode in ["mxfp4", "mxfp8", "nvfp4"]:
            wq, s = mx.quantize(w, mode=mode)

            def mm(s, x, wq):
                return mx.quantized_matmul(x, wq, s, mode=mode).sum()

            # Should raise
            with self.assertRaises(ValueError):
                ds = mx.grad(mm)(s, x, wq)

            rhs_indices = mx.array(0)
            with self.assertRaises(ValueError):

                def gmm(s, x, wq):
                    return mx.gather_qmm(
                        x,
                        wq,
                        s,
                        rhs_indices=rhs_indices,
                        mode=mode,
                    ).sum()

                ds = mx.grad(gmm)(s, x, wq)

    def test_quantize_strided(self):
        N = 64
        mode = "nvfp4"
        w = mx.random.normal(shape=(N, N))
        w_q, scales = mx.quantize(w, mode="nvfp4")

        scales = mx.broadcast_to(mx.array(56, mx.uint8), scales.shape)
        w_hat = mx.dequantize(w_q, scales, mode=mode)
        expected = mx.dequantize(w_q, mx.contiguous(scales), mode=mode)
        self.assertTrue(mx.allclose(w_hat, expected))


if __name__ == "__main__":
    mlx_tests.MLXTestRunner()
