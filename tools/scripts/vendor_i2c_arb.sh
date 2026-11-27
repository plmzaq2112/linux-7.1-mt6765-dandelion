#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== CLK ids ==="
grep -nE "CLK_IFR_I2C[0-9]*(_ARBITER|_IMM)?\b" "$T/include/dt-bindings/clock/mt6765-clk.h" | head -20
echo
echo "=== vendor i2c driver arb handling ==="
grep -nE "arb|ARB" "$V/drivers/i2c/busses/i2c-mt65xx.c" | head -30
echo
echo "=== vendor i2c clock names ==="
grep -nE "devm_clk_get|clock-names|\"main\"|\"dma\"|\"arb\"|\"pmic\"" "$V/drivers/i2c/busses/i2c-mt65xx.c" | head -20
