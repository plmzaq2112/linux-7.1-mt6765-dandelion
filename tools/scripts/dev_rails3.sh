#!/bin/sh
KO=/root/audio/rail_en.ko
for rail in vcn18 vcn28 vldo28 vcamio vcama vfe28 vcn33-bt vcn33-wifi vefuse vrf18; do
    insmod "$KO" name=$rail 2>/dev/null || { echo "rail $rail: insmod failed"; continue; }
    sleep 0.3
    echo "== rail $rail"
    timeout 150 python3 /root/audio/dev_probe3.py 2>&1
    rmmod rail_en 2>/dev/null
done
echo "== no rail extra (baseline)"
timeout 150 python3 /root/audio/dev_probe3.py 2>&1
echo done
