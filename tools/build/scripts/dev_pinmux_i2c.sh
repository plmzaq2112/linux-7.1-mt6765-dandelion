#!/bin/sh
echo "=== pins claimed by i2c controllers ==="
for f in /sys/kernel/debug/pinctrl/*/pinmux-pins; do
    grep -iE "i2c@|1100[0-9a-f]{4}\.i2c" "$f" 2>/dev/null | head -30
done
echo
echo "=== any pin muxed to scp/i2c other function ==="
for f in /sys/kernel/debug/pinctrl/*/pinmux-pins; do
    grep -iE "scp|i2c" "$f" 2>/dev/null | head -40
done
