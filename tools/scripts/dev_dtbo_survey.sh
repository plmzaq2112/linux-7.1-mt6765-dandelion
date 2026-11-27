#!/bin/sh
echo "=== all partitions ==="
ls /dev/disk/by-partlabel/ | tr '\n' ' '
echo
echo
for p in dtbo dtbo_a dtbo_b; do
    [ -e /dev/disk/by-partlabel/$p ] || continue
    echo "== $p size=$(blockdev --getsize64 /dev/disk/by-partlabel/$p 2>/dev/null)"
    dd if=/dev/disk/by-partlabel/$p bs=1M status=none 2>/dev/null \
        | tr -c '[:print:]' '\n' | grep -iE "stk3|alsps|sensor|sc7a|bma2|i2c" | sort -u | head -20
done
