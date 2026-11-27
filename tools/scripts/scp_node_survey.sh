#!/bin/bash
D=/tmp/vendor.dts
echo "=== scp node in vendor dts ==="
awk '/scp@10500000 \{/,/^\t\t\};/' "$D" | head -40
echo
echo "=== vendor kernel: stk3x3x / sensor hub i2c ==="
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
grep -rln "stk3x3x\|stk3338\|STK3X3X" "$V" 2>/dev/null | head -10
echo
echo "=== scp i2c driver? ==="
ls "$V/drivers/misc/mediatek/scp" 2>/dev/null | head -20
find "$V/drivers" -iname "*scp*i2c*" 2>/dev/null | head -10
