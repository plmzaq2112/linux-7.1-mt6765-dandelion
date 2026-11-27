#!/bin/bash
set -e
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
cd "$T"

echo "=== enable CONFIG_RAIL_EN=m ==="
scripts/config --file out/.config -m RAIL_EN
make O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig >/dev/null
grep -n "CONFIG_RAIL_EN" out/.config

echo "=== build drivers/misc modules ==="
make O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" M=drivers/misc modules 2>&1 | tail -12
ls -l out/drivers/misc/rail_en.ko
