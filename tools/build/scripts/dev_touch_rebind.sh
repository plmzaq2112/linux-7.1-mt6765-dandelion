#!/bin/sh
D=/sys/bus/spi/drivers/fts_ts
echo "=== driver dir ==="
ls "$D" 2>/dev/null | head
echo
echo "=== unbind/bind ==="
if [ -e "$D/spi3.0" ]; then
    echo spi3.0 > "$D/unbind" 2>/dev/null && echo "unbound"
fi
sleep 1
echo spi3.0 > "$D/bind" 2>/dev/null; echo "bind rc=$?"
sleep 1
echo
echo "=== dmesg after rebind ==="
dmesg | grep -i "FTS_TS" | tail -12
echo
echo "=== input devices ==="
cat /proc/bus/input/devices | grep -E "^N:" 
