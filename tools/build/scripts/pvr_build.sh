#!/bin/bash
set -e
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
cd "$T"
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- O=out -j"$(nproc)" drivers/misc/pvr/ddk/pvrsrvkm.ko 2>&1 | tail -12
OUT=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/pvrsrvkm-dump.ko
aarch64-linux-gnu-strip --strip-debug out/drivers/misc/pvr/ddk/pvrsrvkm.ko -o "$OUT"
ls -l "$OUT"
