#!/bin/sh
KO=/root/audio/rail_en.ko
for rail in vcn18 vcn28 vldo28 vcamio vcama vfe28 vcn33-bt vcn33-wifi vefuse vrf18 vibr; do
    insmod "$KO" name=$rail 2>/dev/null
    rc=$?
    if [ $rc -ne 0 ]; then
        echo "rail $rail: insmod rc=$rc"
        continue
    fi
    sleep 0.3
    out=$(timeout 90 python3 /root/audio/dev_probe_once.py 2>&1)
    echo "rail $rail: $out"
    rmmod rail_en 2>/dev/null
done
echo done
