#!/bin/sh
echo "=== partitions ==="
cat /proc/partitions
echo
echo "=== by-name ==="
ls /dev/block/by-name 2>/dev/null | head -40
ls /dev/disk/by-partlabel 2>/dev/null | head -40
echo
echo "=== mounts ==="
mount | head -20
echo
echo "=== scp / sensor dmesg ==="
dmesg | grep -iE "scp|sensor|alsps" | head -15
echo
echo "=== dev i2c ==="
ls /dev/i2c-* 2>/dev/null
python3 -c "import sys; print(sys.version)" 2>/dev/null
