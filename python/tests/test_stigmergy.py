import mlx.core as mx
import pytest
from mlx.quant.stigmergy import StigmergicAccumulator, StigmergySnapshot


def test_stigmergy_saturating_ema():
    shape = (32, 32)
    acc = StigmergicAccumulator(
        shape=shape,
        ema_decay=0.2,
        rho_min=0.0,
        rho_max=3.0,
        baseline_rho=0.2,
    )

    # Initial density must be baseline
    assert mx.allclose(acc.density, mx.ones(shape) * 0.2)

    # Ingest massive infinite shock (e.g. crawler loops on a viral node)
    for _ in range(50):
        acc.ingest_event(degrees=10000.0, traversals=50000.0)

    # Density must saturate at rho_max without runaway overflow
    assert float(mx.max(acc.density).item()) <= 3.0
    assert float(mx.min(acc.density).item()) >= 0.0
    assert float(mx.mean(acc.density).item()) > 2.5


def test_stigmergy_snapshot_and_restore():
    shape = (16, 16)
    acc = StigmergicAccumulator(shape=shape, baseline_rho=0.1)

    # Ingest some events
    acc.ingest_event(degrees=10.0, traversals=20.0)
    snap1 = acc.create_snapshot()
    assert snap1.version == 1
    assert snap1.data is not None

    saved_density = mx.array(acc.density)

    # Ingest radically different events
    acc.ingest_event(degrees=500.0, traversals=900.0)
    assert not mx.allclose(acc.density, saved_density)

    # Restore snapshot
    acc.restore_snapshot(snap1)
    assert mx.allclose(acc.density, saved_density)
    assert acc.snapshot_version == 1


def test_stigmergy_baseline_decay():
    shape = (16, 16)
    acc = StigmergicAccumulator(shape=shape, ema_decay=0.5, baseline_rho=0.1)

    # Step 1: Pump density high
    acc.ingest_event(degrees=100.0, traversals=100.0)
    high_density = float(mx.mean(acc.density).item())
    assert high_density > 0.5

    # Step 2: Zero evidence over multiple steps -> should decay back to baseline 0.1
    for _ in range(20):
        acc.ingest_event(degrees=0.0, traversals=0.0)

    relaxed_density = float(mx.mean(acc.density).item())
    assert abs(relaxed_density - 0.1) < 1e-3
