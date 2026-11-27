#!/bin/sh
echo "=== bus -> of_node ==="
for d in /sys/bus/i2c/devices/i2c-*; do
    echo "$(basename $d) -> $(readlink -f $d/of_node 2>/dev/null)"
done
echo
echo "=== clients ==="
for d in /sys/bus/i2c/devices/*-*; do
    [ -e "$d/name" ] || continue
    echo "$(basename $d) name=$(cat $d/name) driver=$(readlink -f $d/driver 2>/dev/null | xargs -r basename)"
done
