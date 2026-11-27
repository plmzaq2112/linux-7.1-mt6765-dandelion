#!/bin/sh
echo "=== pvr dmesg ==="
dmesg | grep -iE 'pvr|rgx|firmware|fault|timeout|watchdog' | tail -30
echo "=== modules ==="
lsmod | grep pvrsrvkm
