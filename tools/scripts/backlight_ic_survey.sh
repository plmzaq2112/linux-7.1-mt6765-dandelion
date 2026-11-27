#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"

echo "=== vendor backlight configs ==="
grep -nE "LM3697|MT6370|BACKLIGHT|BLED|LEDS_MT" "$V/arch/arm64/configs/stock_defconfig" | head -20
echo
echo "=== mainline panel driver ==="
ls "$T/drivers/gpu/drm/panel/" | grep -iE "fitipower|ft8006|dandelion" | head
f=$(ls "$T/drivers/gpu/drm/panel/" | grep -iE "fitipower|ft8006" | head -1)
if [ -n "$f" ]; then
    grep -nE "backlight|brightness|dsi|drm_panel" "$T/drivers/gpu/drm/panel/$f" | head -20
fi
echo
echo "=== vendor panel driver backlight/brightness ==="
find "$V/drivers" -iname "*ft8006*" -o -iname "*fitipower*" 2>/dev/null | head -5
for f in $(find "$V/drivers" -iname "*ft8006*" 2>/dev/null | head -2); do
    echo "--- ${f#$V/}"
    grep -nE "backlight|brightness|dsi" "$f" | head -15
done
