#!/bin/sh
echo "=== /dev/dri ==="
ls -l /dev/dri/
echo "=== sysfs drm ==="
ls /sys/class/drm/ 2>/dev/null
echo "=== connector status ==="
for f in /sys/class/drm/*/status; do
  echo "$f: $(cat $f 2>/dev/null)"
done
echo "=== card driver ==="
for d in /sys/class/drm/card*; do
  [ -e "$d/device/driver" ] || continue
  echo "$d -> $(basename $(readlink -f $d/device/driver))"
done
