#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
F="$T/include/dt-bindings/pinctrl/mediatek,mt6765-pinfunc.h"
echo "=== distinct I2C pin functions ==="
grep -oE "FUNC_S[CD][LA][0-9_]*" "$F" | sort -u
echo
echo "=== pins for SCL7/8/9 (if any) ==="
grep -nE "SCL[789]|SDA[789]" "$F" | head -20
echo
echo "=== mt6765 i2c nodes in mainline dtsi ==="
grep -cE "i2c[0-9]+: i2c@" "$T/arch/arm64/boot/dts/mediatek/mt6765.dtsi"
grep -nE "i2c[0-9]+: i2c@" "$T/arch/arm64/boot/dts/mediatek/mt6765.dtsi"
