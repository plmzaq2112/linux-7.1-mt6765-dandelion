#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
S="$V/drivers/misc/mediatek/sensors-1.0"
echo "=== sensors tree ==="
ls "$S" 2>/dev/null
echo
echo "=== alsps dir ==="
ls "$S/alsps" 2>/dev/null
echo
echo "=== cust_alsps headers ==="
find "$S" -name "cust_alsps*" | head -20
echo
echo "=== which ALSPS chip is selected (ProjectConfig) ==="
grep -rn "CUST_ALSPS_SUPPORT\|ALSPS" "$V/arch/arm64/configs/blossom_defconfig" 2>/dev/null | head -20
echo
echo "=== vendor dts around board-sensor ==="
sed -n '455,485p' /tmp/vendor.dts
