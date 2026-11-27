#!/bin/sh
echo "=== spi3 node ==="
ls /proc/device-tree/soc/spi@11013000/ 2>/dev/null
for c in /proc/device-tree/soc/spi@11013000/*/; do
    echo "-- child: $c"
    ls "$c"
done

echo
echo "=== touch props (strings) ==="
for f in /proc/device-tree/soc/spi@11013000/*focal*/*; do
    [ -f "$f" ] || continue
    echo "-- $(basename $f)"
    od -An -tx1 "$f" | head -2
done

echo
echo "=== spi3 status/pinctrl ==="
for f in status pinctrl-0 pinctrl-names cs-gpios; do
    [ -f "/proc/device-tree/soc/spi@11013000/$f" ] && { echo "-- $f"; od -An -tx1 "/proc/device-tree/soc/spi@11013000/$f" | head -2; }
done

echo
echo "=== regulators related to lcd/touch ==="
dmesg | grep -iE "regulator|vcam|vcn|vddi|tp_" | head -20

echo
echo "=== gpio 154 / touch gpios ==="
cat /sys/kernel/debug/gpio | grep -E "gpio-1[0-9]{2} |gpio-6[0-9] " | head -20
