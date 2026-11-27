#!/bin/bash
W="/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
F="$W/dist/phone.fdt"
D=/tmp/mt6370.dts
dtc -I dtb -O dts -o "$D" "$F" 2>/dev/null

echo "=== mt6370-backlight node ==="
grep -n 'mt6370-backlight' -B5 -A30 "$D" | head -50
echo
echo "=== mt6370 MFD node ==="
grep -n 'pmic@34' -A40 "$D" | head -60
echo
echo "=== mainline mt6370 drivers ==="
grep -rln "mt6370" "$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers" 2>/dev/null | head -20
echo
echo "=== mainline config ==="
grep -nE "MT6370" "$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline/out/.config"
echo
echo "=== vendor mt6370 backlight ==="
find "$V/drivers" -iname "*mt6370*" 2>/dev/null | head -20
