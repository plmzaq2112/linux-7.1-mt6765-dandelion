#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
echo "=== grep 2047 in vendor configs ==="
grep -rn "BACKLIGHT_SUPPORT_2047" "$V/arch/arm64/configs/" 2>/dev/null | head -10
echo
echo "=== grep 2047 anywhere in vendor kernel config files ==="
grep -rln "BACKLIGHT_SUPPORT_2047" "$V" --include="*defconfig*" --include="*config*" 2>/dev/null | head -10
echo
echo "=== lcm dir ProjectConfig ==="
ls "$V/drivers/misc/mediatek/lcm/" 2>/dev/null | head -20
echo
echo "=== which lcm is selected for dandelion ==="
grep -rn "ft8006s" "$V/drivers/misc/mediatek/lcm/"*.mk "$V/drivers/misc/mediatek/lcm/Makefile" 2>/dev/null | head -10
