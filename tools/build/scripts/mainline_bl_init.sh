#!/bin/bash
F="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/gpu/drm/panel/panel-fitipower-ft8006s.c"
grep -n "0x51\|0xff\|0xb8" "$F" | head -20
echo "=== context around 0x51 ==="
grep -n "0x51" "$F" | cut -d: -f1 | while read -r l; do
    s=$((l-6)); e=$((l+6))
    echo "--- line $l"
    sed -n "${s},${e}p" "$F"
done
