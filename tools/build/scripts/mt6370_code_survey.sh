#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"

echo "=== mainline mt6370 vendor check ==="
grep -n "vendor\|CHIP_ID\|chip_id\|ENXIO" "$T/drivers/mfd/mt6370.c" | head -30
echo
sed -n "$(grep -n 'check_vendor' "$T/drivers/mfd/mt6370.c" | head -1 | cut -d: -f1),+40p" "$T/drivers/mfd/mt6370.c"

echo
echo "=== mainline backlight driver ==="
grep -n "compatible\|max_brightness\|brightness" "$T/drivers/video/backlight/mt6370-backlight.c" | head -20

echo
echo "=== vendor core chip id ==="
grep -n "vendor\|CHIP_ID\|chip_id\|0x" "$V/drivers/misc/mediatek/pmic/mt6370/mt6370_pmu_core.c" | head -25
