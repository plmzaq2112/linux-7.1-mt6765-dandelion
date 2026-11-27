#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
P="/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A"

echo "=== vendor mt6370 core: power/regulator ==="
grep -nE "regulator|vcn18|vio18|vusb|power_on|reset|gpio" "$V/drivers/misc/mediatek/pmic/mt6370/mt6370_pmu_core.c" | head -30
echo
echo "=== vendor mt6370 i2c ==="
grep -nE "i2c|bank|addr" "$V/drivers/misc/mediatek/pmic/mt6370/mt6370_pmu_i2c.c" | head -20

echo
echo "=== stock logs mt6370 ==="
grep -rniE "mt6370|mt6370_pmu|bled" "$P" --include="*.txt" --include="*.log" 2>/dev/null | head -15
