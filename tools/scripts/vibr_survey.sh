#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== vibrator drivers in mainline ==="
grep -rln "vibrator" "$T/drivers/input/misc" "$T/drivers/misc" 2>/dev/null | head -10
echo
echo "=== gpio-vibra bindings ==="
ls "$T/Documentation/devicetree/bindings/input/" 2>/dev/null | grep -i vib
echo
echo "=== gpio-vibra compatible ==="
grep -nE "compatible|supply|enable-gpios|vcc" "$T/drivers/input/misc/gpio-vibra.c" 2>/dev/null | head -20
echo
echo "=== vendor vibrator driver ==="
find "$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/drivers" -ipath "*vibrat*" -name "*.c" | head -5
