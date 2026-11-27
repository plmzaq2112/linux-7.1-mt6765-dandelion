#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
echo "=== vendor mt6765.dtsi i2c nodes: clock-names ==="
awk '/i2c[0-9]*: i2c@1100[0-9a-f]+ \{/,/^\t\t\};/' "$V/arch/arm64/boot/dts/mediatek/mt6765.dtsi" | grep -E "i2c[0-9]*: i2c@|clock-names|clocks =" | head -40
echo
echo "=== any 'arb' in vendor dts ==="
grep -rn "\"arb\"" "$V/arch/arm64/boot/dts/mediatek/" | head -10
