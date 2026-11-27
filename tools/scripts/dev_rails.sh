#!/bin/sh
# usage: dev_rails.sh  (expects rail_en.ko in /root/audio/)
KO=/root/audio/rail_en.ko
SCAN=/root/audio/dev_probe_once.py

for rail in vcn18 vcn28 vldo28 vcamio vcama vfe28 vcn33-bt vcn33-wifi vefuse vrf18 vibr; do
    if [ -e /sys/class/regulator/regulator.*/name ]; then :; fi
    insmod "$KO" name=$rail 2>/dev/null
    rc=$?
    if [ $rc -ne 0 ]; then
        echo "rail $rail: insmod failed rc=$rc"
        continue
    fi
    sleep 0.3
    echo "== rail $rail enabled"
    timeout 60 python3 "$SCAN"
    rmmod rail_en 2>/dev/null
    sleep 0.1
done
