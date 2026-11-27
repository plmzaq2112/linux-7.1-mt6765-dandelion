#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
echo "=== dandelion defconfigs ==="
ls "$V/arch/arm64/configs" | grep -i dandelion
echo
for f in "$V"/arch/arm64/configs/*dandelion*; do
    [ -f "$f" ] || continue
    echo "-- $(basename $f)"
    grep -nE "ALSPS|ACCEL|GSENSOR|STK3|SC7A|BMA|SENSOR_HUB|MSENSOR" "$f" | head -25
done
