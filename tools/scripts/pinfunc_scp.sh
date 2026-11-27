#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
F=$(ls "$T"/arch/arm64/boot/dts/mediatek/mt6765-pinfunc.h 2>/dev/null || ls "$T"/include/dt-bindings/pinctrl/mt6765-pinfunc.h 2>/dev/null)
echo "pinfunc: $F"
grep -nE "SCP|I2C" "$F" | head -40
