#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== mfd probe / supply ==="
grep -n "phy-supply\|devm_regulator\|regulator_get\|i2c\[" "$T/drivers/mfd/mt6370.c" | head -30
echo
sed -n "$(grep -n 'static int mt6370_probe' "$T/drivers/mfd/mt6370.c" | cut -d: -f1),+60p" "$T/drivers/mfd/mt6370.c"
echo
echo "=== phandle 0x1f ==="
F="/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/dist/phone.fdt"
D=/tmp/mt6370b.dts
dtc -I dtb -O dts -o "$D" "$F" 2>/dev/null
grep -n 'phandle = <0x1f>' -B12 -A6 "$D" | head -30
