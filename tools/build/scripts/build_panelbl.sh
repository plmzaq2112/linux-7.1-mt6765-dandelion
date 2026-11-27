#!/bin/bash
set -e
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
cd "$T"
make O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image.gz modules 2>&1 | tail -30
ls -l out/arch/arm64/boot/Image.gz
