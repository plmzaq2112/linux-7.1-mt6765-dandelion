#!/bin/sh
# patch rcS on p41 (run inside TWRP via adb shell)
R=/mnt/p41/etc/init.d/rcS

if [ ! -f "$R" ]; then
  echo "rcS not found"
  exit 1
fi

if grep -q "timeout 20 udevadm trigger" "$R"; then
  echo "already patched"
else
  sed -i 's|^\[ -x /sbin/udevadm \] && udevadm trigger 2>/dev/null && udevadm settle 2>/dev/null|timeout 20 udevadm trigger 2>/dev/null\ntimeout 20 udevadm settle 2>/dev/null|' "$R"
  echo "patched:"
fi

grep -n "udevadm" "$R"
