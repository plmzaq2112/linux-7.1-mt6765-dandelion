#!/bin/sh
KO=/root/audio/rail_en.ko
SCAN=/root/audio/dev_scan_gpio.py
echo "== baseline"
timeout 120 python3 $SCAN
for rail in vcn18 vcn28 vldo28 vcamio vcama vcamd vfe28 vcn33-bt vcn33-wifi vefuse vrf18 vsim1 vsim2; do
    insmod "$KO" name=$rail 2>/dev/null || { echo "rail $rail: insmod failed"; continue; }
    sleep 0.3
    out=$(timeout 120 python3 $SCAN 2>&1 | tr '\n' ' ')
    echo "rail $rail: $out"
    rmmod rail_en 2>/dev/null
done
echo done
