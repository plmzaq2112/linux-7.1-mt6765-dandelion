#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
S="$V/drivers/misc/mediatek/sensors-1.0"
echo "=== cust_sensorHub.h ==="
sed -n '1,80p' "$S/sensorHub/inc_v1/cust_sensorHub.h"
echo
echo "=== SCP_nanoHub.c: bus/i2c refs ==="
grep -nE "i2c|bus|scp_|IPI|sensor" "$S/sensorHub/SCP_nanoHub/SCP_nanoHub.c" | head -25
echo
echo "=== auto2712p1v1 sensor node sample ==="
grep -n -A12 "cust_alsps\|alsps@" "$V/arch/arm64/boot/dts/mediatek/auto2712p1v1-common.dtsi" | head -40
