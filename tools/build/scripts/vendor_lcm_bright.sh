#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/drivers/misc/mediatek/lcm"
for f in "$V"/ft8006s*/*.c; do
    echo "== $(basename $f)"
    grep -n "0x51" "$f" | head -8
    echo "-- brl/brightness refs:"
    grep -ni "brightness\|set_backlight\|bl_level" "$f" | head -12
done
