#!/bin/bash
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
D=/tmp/v3.dts
dtc -I dtb -O dts -o "$D" "$W/dist/phone.fdt" 2>/dev/null || exit 1
echo "=== vibrator node ==="
grep -n "vibrator" "$D" | head -10
echo
awk '/vibrator \{|vibrator@0 \{/,/};/' "$D" | head -30
echo
echo "=== vibr regulator / gpio refs ==="
grep -nE "vibr|vib_|vibration" "$D" | head -20
