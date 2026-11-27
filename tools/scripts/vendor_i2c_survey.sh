#!/bin/bash
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
D=/tmp/vendor.dts
[ -f "$D" ] || dtc -I dtb -O dts -o "$D" "$W/dist/phone.fdt" 2>/dev/null
echo "=== i2c controllers in vendor dts ==="
grep -nE "i2c@[0-9a-f]+ \{" "$D"
echo
echo "=== i2c child nodes with reg (possible sensors) ==="
grep -nE "^\s+[a-z0-9_-]+@[0-9a-fA-F]+ \{" "$D" | head -40
echo
echo "=== sensor / alsps compatible strings ==="
grep -nE "compatible = .*(sensor|alsps|stk3|accel|gsensor|msensor)" "$D" | head -20
