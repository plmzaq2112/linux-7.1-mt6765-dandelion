#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
echo "=== dandelion dts in vendor tree ==="
find "$V/arch/arm64/boot/dts" -iname "*dandelion*" | head -10
echo
echo "=== any dts with alsps/sensor i2c_num ==="
grep -rln "i2c_num\|alsps\|stk3x1x\|stk3x3x" "$V/arch/arm64/boot/dts" 2>/dev/null | head -10
echo
echo "=== sensor nodes in dandelion dts (if any) ==="
for f in $(find "$V/arch/arm64/boot/dts" -iname "*dandelion*.dts" | head -3); do
    echo "-- $f"
    grep -nE "sensor|alsps|gsensor|acceler|stk|sc7|bma" "$f" | head -10
done
