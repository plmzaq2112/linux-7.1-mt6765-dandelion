#!/bin/sh
ls /sys/kernel/debug/pinctrl/ 2>/dev/null
for d in /sys/kernel/debug/pinctrl/*/; do
    echo "== $d"
    cat "$d/gpio-ranges" 2>/dev/null | head -8
done
