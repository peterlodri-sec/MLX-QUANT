#!/bin/bash
set -e

echo "🌌 MLX-QUANT: Galvanizing TPU Expansion Sequence..."

# 1. Provision the Colab VM
echo "[*] Provisioning TPU v2-8 from Google Colab Backend..."
colab new -s galactic_tpu --tpu v2-8

# 2. Mount Google Drive for persistent weights
echo "[*] Engaging I/O Blackhole: Mounting Google Drive..."
colab drivemount -s galactic_tpu /content/drive

# 3. Execute the Qwen Training script natively on the TPU
echo "[*] Triggering Qwen2.5 Gravitational Lensing (Training)..."
colab exec -s galactic_tpu -f scripts/galactic_qwen_tpu.py

# 4. Export Logs
colab log -s galactic_tpu -o qwen_galactic_expansion.md

# 5. Clean up the Universe
echo "[*] Tearing down the VM..."
colab stop -s galactic_tpu

echo "✅ Expansion complete. Check qwen_galactic_expansion.md for the training logs."
