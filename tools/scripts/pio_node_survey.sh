#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
F="/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/dist/phone.fdt"
D=/tmp/pio.dts
dtc -I dtb -O dts -o "$D" "$F" 2>/dev/null

echo "=== pinmux encoding ==="
grep -rn "PIN_NO\|FUNC_NO" "$T/drivers/pinctrl/mediatek/pinctrl-paris.h" "$T/drivers/pinctrl/mediatek/pinctrl-paris.c" 2>/dev/null | head -10
echo
echo "=== pio node ==="
grep -n "pinctrl@10005000" -A25 "$D" | head -40
echo
echo "=== sample pinctrl child node ==="
grep -n "pinctrl@10005000" -A120 "$D" | grep -nE "[a-z0-9_]+: [a-z0-9_-]+ \{|pinmux = " | head -20
