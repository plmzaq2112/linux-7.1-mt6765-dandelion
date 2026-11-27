#!/bin/sh
echo "=== uname ==="
uname -r
echo
echo "=== input devices ==="
cat /proc/bus/input/devices | grep -E "^N:|^H:" | head -20
echo
echo "=== lsmod (touch/spi) ==="
lsmod | grep -iE "focal|fts|spi" 
echo
echo "=== dmesg touch ==="
dmesg | grep -iE "focal|fts_ts|touch" | tail -15
echo
echo "=== module vermagic ==="
modinfo focaltech_ts 2>/dev/null | grep -E "vermagic|filename"
echo
echo "=== module dir ==="
ls /lib/modules/ 2>/dev/null
ls /lib/modules/$(uname -r)/extra 2>/dev/null | head
