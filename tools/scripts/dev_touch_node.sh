#!/bin/sh
echo "=== spi3 children ==="
ls -d /proc/device-tree/soc/spi@11013000/*/ 2>/dev/null
echo
for d in /proc/device-tree/soc/spi@11013000/*/; do
    echo "-- $d"
    ls "$d"
done

echo
echo "=== pinctrl pinmux 174 / 178 / 180 ==="
for p in /sys/kernel/debug/pinctrl/*/pinmux-pins; do
    grep -E "pin 174 |pin 178 |pin 180 " "$p" 2>/dev/null
done

echo
echo "=== fts full dmesg ==="
dmesg | grep -i "FTS_TS" | head -30

echo
echo "=== spi3 cs / irq in DT ==="
od -An -tx1 /proc/device-tree/soc/spi@11013000/spi-max-frequency 2>/dev/null
