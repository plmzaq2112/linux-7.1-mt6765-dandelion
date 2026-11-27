#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
S="$V/drivers/misc/mediatek/sensors-1.0"
echo "=== sensors-1.0 tree (depth 3) ==="
find "$S" -maxdepth 3 -type d | sed "s|$S|.|" | sort | head -40
echo
echo "=== any stk/bma/sc7 source in whole vendor tree ==="
grep -rliE "stk3x|stk3338|sc7a20|bma2x2" "$V" --include="*.c" --include="*.h" --include="*.dtsi" --include="*.dts" --include="*.mk" --include="*.config" 2>/dev/null | head -20
echo
echo "=== nanohub / sensorhub files ==="
find "$S/sensorHub" -maxdepth 3 -type f | head -30
