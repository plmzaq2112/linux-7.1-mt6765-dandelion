#!/bin/sh
echo "=== i2c clients ==="
for d in /sys/bus/i2c/devices/*; do
    case "$d" in
    */i2c-*) continue;;
    esac
    echo "$(basename $d)  name=$(cat $d/name 2>/dev/null)"
done

echo
echo "=== i2c adapter speeds ==="
for d in /sys/bus/i2c/devices/i2c-*; do
    echo "$(basename $d): $(cat $d/of_node/clock-frequency 2>/dev/null | od -An -tx1 | tr -d ' \n')"
done

echo
echo "=== dmesg i2c ==="
dmesg | grep -iE "i2c|mt65xx" | tail -20

echo
echo "=== vendor dts: which i2c are okay ==="
for n in 11007000 11008000 11009000 1100f000 11011000 1100d000 11016000; do
    s=$(tr -d '\0' < /proc/device-tree/soc/i2c@$n/status 2>/dev/null)
    echo "i2c@$n status=$s"
done
