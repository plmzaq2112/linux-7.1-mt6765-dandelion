#!/bin/bash
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
D=/tmp/v4.dts
dtc -I dtb -O dts -o "$D" "$W/dist/phone.fdt" 2>/dev/null || exit 1
echo "=== pinctrl groups with i2c/sensor/als names ==="
grep -nE "^\s+[a-z0-9_]*(i2c|sensor|als|gsensor|ps)[a-z0-9_]* \{" "$D" | head -30
echo
echo "=== any scp pin function ==="
grep -niE "scp.*(scl|sda)|(scl|sda).*scp" "$D" | head -10
echo
echo "=== i2c pin groups (pins property) ==="
grep -nB2 -A6 "pins = \"scl\"\|pins = \"sda\"" "$D" | head -40
