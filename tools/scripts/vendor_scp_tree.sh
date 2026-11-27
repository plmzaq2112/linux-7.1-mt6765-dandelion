#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
echo "=== scp tree ==="
find "$V/drivers/misc/mediatek/scp" -maxdepth 2 -type f | head -20
echo
echo "=== scp: i2c / sensor refs ==="
grep -rnE "i2c|sensor" "$V/drivers/misc/mediatek/scp" 2>/dev/null | head -20
echo
echo "=== any scp firmware images in tree ==="
find "$V" -iname "*scp*.img" -o -iname "*scp*.bin" 2>/dev/null | head -10
echo
echo "=== any 'sensor' config files in vendor tree root dirs ==="
find "$V" -maxdepth 2 -type d | head -25
