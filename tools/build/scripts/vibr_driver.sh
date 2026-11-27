#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== driver exists? ==="
ls -l "$T/drivers/input/misc/regulator-vibrator.c" 2>/dev/null
echo
echo "=== DT bindings / props ==="
sed -n '1,60p' "$T/Documentation/devicetree/bindings/input/regulator-vibrator.yaml" 2>/dev/null
echo
echo "=== config ==="
grep -nE "CONFIG_REGULATOR_VIBRATOR|CONFIG_INPUT_GPIO_VIBRA" "$T/out/.config"
echo
echo "=== driver of_match ==="
grep -nE "of_match|compatible|regulator|volt|period|supply" "$T/drivers/input/misc/regulator-vibrator.c" 2>/dev/null | head -30
