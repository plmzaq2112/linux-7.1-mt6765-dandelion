#!/bin/sh
for d in /sys/kernel/debug/asoc/mt6765-evk/*/; do
    echo "== $d"
    ls "$d/dapm" 2>/dev/null | head -30
done
echo "=== card dapm ==="
ls /sys/kernel/debug/asoc/mt6765-evk/dapm 2>/dev/null
