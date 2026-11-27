#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
cd "$T"
echo "=== files ==="
ls -l drivers/misc/rail_en.c 2>/dev/null
tail -3 drivers/misc/Makefile
echo
echo "=== auto.conf ==="
grep -n "RAIL_EN" out/include/config/auto.conf out/.config 2>/dev/null
echo
echo "=== build verbose ==="
make O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- M=drivers/misc modules 2>&1 | grep -iE "rail|error" | head -20
echo
find out -name "rail_en.ko" 2>/dev/null
