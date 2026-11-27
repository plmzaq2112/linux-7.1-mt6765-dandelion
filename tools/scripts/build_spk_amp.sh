#!/bin/bash
set -e
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
cd "$T"

echo "=== modules_prepare ==="
make O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" modules_prepare 2>&1 | tail -15

echo "=== build module ==="
make O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" \
    sound/soc/mediatek/mt6765/mt6765-mt6357.ko 2>&1 | tail -30

ls -l out/sound/soc/mediatek/mt6765/mt6765-mt6357.ko
