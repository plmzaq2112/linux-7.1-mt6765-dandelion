#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/drivers/leds/regulator-vibrator.c"
echo "=== DT props parsed ==="
sed -n '/mt_vibra_parse_dt/,/^}/p' "$V" | head -80
echo
echo "=== binding doc ==="
cat "$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/Documentation/devicetree/bindings/leds/regulator-vibrator.txt"
