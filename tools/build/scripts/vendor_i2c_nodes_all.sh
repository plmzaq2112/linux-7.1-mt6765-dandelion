#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
echo "=== all i2c node bases in vendor dts(ides) ==="
grep -rhoE "i2c@[0-9a-f]{8}" "$V/arch/arm64/boot/dts/mediatek/" 2>/dev/null | sort -u
echo
echo "=== i2c7/8/9 labels ==="
grep -rnE "i2c7:|i2c8:|i2c9:" "$V/arch/arm64/boot/dts/mediatek/" 2>/dev/null | head -10
echo
echo "=== mt6765 dtsi file? ==="
ls "$V/arch/arm64/boot/dts/mediatek/" | grep -iE "6765|6762" | head -10
