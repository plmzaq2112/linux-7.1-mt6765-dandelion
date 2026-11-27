#!/bin/bash
F="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline/include/dt-bindings/pinctrl/mediatek,mt6765-pinfunc.h"
for p in 48 49 50 51 81 82 83 84 103 104 105 106 161 162; do
    echo "-- GPIO$p"
    grep -E "MTK_PIN_NO\($p\)" "$F" | sed -e 's/^#define PINMUX_//' -e 's/ .*$//'
done
