#!/bin/sh
echo "=== pins 4-7 ==="
for f in /sys/kernel/debug/pinctrl/*/pinmux-pins; do
    grep -E "pin (4|5|6|7) " "$f"
done
echo
echo "=== pins 13-24 ==="
for f in /sys/kernel/debug/pinctrl/*/pinmux-pins; do
    grep -E "pin (1[3-9]|2[0-4]) " "$f"
done
echo
echo "=== spi controllers ==="
ls /sys/class/spi_master/ 2>/dev/null
for s in /sys/class/spi_master/*; do echo "$(basename $s) -> $(readlink -f $s/device/of_node 2>/dev/null)"; done
