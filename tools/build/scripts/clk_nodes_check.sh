#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
D="$T/../../kernel_7.1_mainline/logs/v17/v17.dts"
D=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/v17/v17.dts
echo "=== CLK_IFR_AP_DMA id ==="
grep -nE "CLK_IFR_AP_DMA|CLK_IFR_I2C_AP" "$T/include/dt-bindings/clock/mt6765-clk.h"
echo
echo "=== infracfg / topckgen nodes in boot dtb ==="
grep -nB3 -A12 "mediatek,mt6765-infracfg\|mt6765-infrasys\|mediatek,mt6765-topckgen\|mt6765-topckgen" "$D" | head -60
echo
echo "=== what phandle is 0x16 ==="
grep -n "phandle = <0x16>;" "$D"
