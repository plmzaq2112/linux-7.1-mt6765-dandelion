#!/bin/sh
N=/sys/class/power_supply/bq256xx-charger/of_node
echo "=== of_node ==="
readlink -f "$N" 2>/dev/null
cat "$N/compatible" 2>/dev/null | tr -d '\0'; echo
echo "=== charger nodes in DT ==="
find /proc/device-tree -type d \( -name '*bq*' -o -name '*charger*' \) 2>/dev/null | head -10
echo "=== usb connector node ==="
find /proc/device-tree -type d -name 'connector' 2>/dev/null | head
echo "=== vbus supply phandle ==="
C=$(find /proc/device-tree -type d -name 'connector' 2>/dev/null | head -1)
if [ -n "$C" ]; then ls "$C"; fi
