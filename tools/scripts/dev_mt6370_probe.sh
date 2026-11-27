#!/bin/sh
echo "=== i2cget 0x34 ==="
which i2cget 2>/dev/null || echo no-i2cget
i2cget -y 5 0x34 0x00 2>&1 | head -2
echo
echo "=== i2c3? bus5 devices ==="
ls /sys/bus/i2c/devices/5-0034
echo
echo "=== regulators (vio18 etc) ==="
for r in /sys/class/regulator/*; do
    n=$(cat $r/name 2>/dev/null)
    case "$n" in
        *vio18*|*vcn18*|*vaud28*|*vcn33*|*vmc*|*vldo28*|*vs1*)
            echo "$n: state=$(cat $r/state 2>/dev/null)";;
    esac
done
echo
echo "=== mt6370 dmesg ==="
dmesg | grep -i mt6370 | tail -5
