#!/bin/sh
echo "=== regulators with usb/33/18 ==="
for r in /sys/class/regulator/*; do
    n=$(cat "$r/name" 2>/dev/null)
    case "$n" in
        *usb*|*33*|*18*|*vio*|*vcn*)
            echo "$n: $(cat $r/state 2>/dev/null)";;
    esac
done
echo
echo "=== all regulator names ==="
for r in /sys/class/regulator/*; do cat "$r/name" 2>/dev/null; done | sort | head -40
