#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
F="$T/drivers/i2c/busses/i2c-mt65xx.c"
echo "=== arb clock handling ==="
grep -nE "ARB|arb|I2C_MT65XX_CLK_ARB|SET_MASTER|arbiter" "$F" | head -30
echo
echo "=== enable/disable clocks ==="
sed -n '/mtk_i2c_clock_enable/,/^}/p' "$F" | head -40
echo
echo "=== mainline dtsi i2c2 clocks ==="
grep -n -A12 "i2c2: i2c@11009000" "$T/arch/arm64/boot/dts/mediatek/mt6765.dtsi"
