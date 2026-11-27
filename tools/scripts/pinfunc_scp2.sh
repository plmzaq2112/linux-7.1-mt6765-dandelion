#!/bin/bash
F="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline/include/dt-bindings/pinctrl/mediatek,mt6765-pinfunc.h"
echo "=== SCP / I2C mux options ==="
grep -nE "SCP|I2C" "$F" | head -40
echo
echo "=== all distinct function suffixes ==="
grep -oE "_FUNC_[A-Z0-9_]+" "$F" | sort -u | head -60
