#!/bin/bash
F="/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/dist/phone.fdt"
D=/tmp/pw.dts
dtc -I dtb -O dts -o "$D" "$F" 2>/dev/null || { echo dtc failed; exit 1; }
echo "=== phandle 0xa3 node ==="
grep -n 'phandle = <0xa3>' -B12 -A12 "$D" | head -40
echo
echo "=== pwm nodes ==="
grep -nE 'pwm@|disp_pwm|compatible = "mediatek.*pwm' "$D" | head -15
echo
echo "=== pwm node details ==="
grep -n 'pwm@1100e000' -A25 "$D" | head -35
echo
echo "=== backlight panel props ==="
grep -n 'backlight' "$D" | head -10
