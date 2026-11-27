#!/bin/sh
echo "=== backlight ==="
ls /sys/class/backlight
for b in /sys/class/backlight/*; do
    [ -e "$b" ] || continue
    echo "$b max=$(cat "$b/max_brightness" 2>/dev/null) cur=$(cat "$b/brightness" 2>/dev/null)"
done
echo
echo "=== i2c devices ==="
ls /sys/bus/i2c/devices | head -30
echo
echo "=== i2c scan (skip bus 3) ==="
for b in 0 1 2 4 5 6; do
    echo "--- i2c-$b"
    timeout 4 python3 /root/audio/i2c_scan.py "$b" 2>&1 | head -8
done
echo
echo "=== iio ==="
for d in /sys/bus/iio/devices/*; do
    echo "$d: $(cat $d/name 2>/dev/null)"
done
echo
echo "=== fdt copy ==="
cp /sys/firmware/fdt /root/phone.fdt && ls -l /root/phone.fdt
