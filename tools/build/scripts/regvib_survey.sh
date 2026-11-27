#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
echo "=== mainline: regulator-vibrator ==="
grep -rln "regulator-vibrator" "$T" 2>/dev/null | head -10
echo
echo "=== vendor driver header ==="
sed -n '1,60p' "$V/drivers/leds/regulator-vibrator.c"
echo
echo "=== vendor DT binding for it ==="
grep -rn "regulator-vibrator" "$V/Documentation" 2>/dev/null | head -5
grep -rn "vib_vol\|vib-period\|max-volt" "$V/drivers/leds/regulator-vibrator.c" | head -10
