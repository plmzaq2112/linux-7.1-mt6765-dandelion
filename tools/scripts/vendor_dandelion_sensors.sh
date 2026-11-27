#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/arch/arm64/boot/dts/mediatek"
echo "=== dandelion dir ==="
ls "$V/dandelion" 2>/dev/null | head -20
echo
echo "=== sensor keywords across dandelion dts ==="
grep -rniE "alsps|gsensor|sensor|stk3|sc7a|bma2|accel|hwmsen|light" "$V/dandelion" "$V/dandelion.dts" 2>/dev/null | head -30
echo
echo "=== i2c children with reg 0x48/0x19/0x18 in dandelion ==="
grep -rnE "@(48|19|18|1e|38|39|53) \{" "$V/dandelion" "$V/dandelion.dts" 2>/dev/null | head -20
