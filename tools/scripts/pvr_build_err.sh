#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
cd "$T" || exit 1
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- O=out -j"$(nproc)" \
    drivers/misc/pvr/ddk/pvrsrvkm.ko 2>&1 | grep -E "error:|warning: .*dmabuf|Error" | head -25
