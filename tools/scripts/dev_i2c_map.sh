#!/bin/sh
echo "=== i2c bus map ==="
for d in /sys/bus/i2c/devices/i2c-*; do
    [ -e "$d/name" ] || continue
    echo "$(basename $d)  $(cat $d/name)"
done

echo
echo "=== MT6370 node status in live DTB ==="
for n in /proc/device-tree/soc/i2c@11016000; do
    echo "-- $n"
    [ -f "$n/status" ] && cat "$n/status" | tr -d '\0' && echo
    ls "$n" 2>/dev/null | head
done

echo
echo "=== probe 0x34 on every bus ==="
command -v i2cdetect >/dev/null 2>&1 && echo "have i2cdetect" || echo "no i2cdetect"
for d in /sys/bus/i2c/devices/i2c-*; do
    n=${d##*-}
    [ -f "$d/name" ] || continue
    echo "bus $n ($(cat $d/name))"
done
