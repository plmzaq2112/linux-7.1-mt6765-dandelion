#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== mainline mt6765.dtsi i2c nodes ==="
awk '/i2c[0-9]*: i2c@1100[0-9a-f]+ \{/,/^\t\t\};/' "$T/arch/arm64/boot/dts/mediatek/mt6765.dtsi" | head -60
echo
echo "=== mainline clk ids (i2c) ==="
grep -nE "I2C|IFR" "$T/include/dt-bindings/clock/mt6765-clk.h" | head -25
