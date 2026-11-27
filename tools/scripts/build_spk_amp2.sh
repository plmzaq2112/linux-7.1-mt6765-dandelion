#!/bin/bash
set -e
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
cd "$T"

make O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- KBUILD_MODPOST_WARN=1 -j"$(nproc)" \
    sound/soc/mediatek/mt6765/mt6765-mt6357.ko 2>&1 | tail -15

ls -l out/sound/soc/mediatek/mt6765/mt6765-mt6357.ko
modinfo out/sound/soc/mediatek/mt6765/mt6765-mt6357.ko 2>/dev/null | head -8
