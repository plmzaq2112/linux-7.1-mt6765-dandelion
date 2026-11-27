#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"

echo "=== macro defs ==="
grep -rn "define MTK_PIN_NO\|define MTK_FUNCTION" "$T/drivers/pinctrl/mediatek/" "$V/drivers/pinctrl/mediatek/" 2>/dev/null | head -6
echo
echo "=== pin 43 in mainline table ==="
grep -n "GPIO43" -A10 "$T/drivers/pinctrl/mediatek/pinctrl-mtk-mt6765.h" | head -15
echo
echo "=== running dtb pinmux for pin43 ==="
F="/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/dist/phone.fdt"
D=/tmp/pin43.dts
dtc -I dtb -O dts -o "$D" "$F" 2>/dev/null
grep -n "pinmux = <0x2b" "$D" | head -10
grep -n "0x2b01\|0x2b00" "$D" | head -5
echo
echo "=== vendor pinfunc header? ==="
ls "$V/arch/arm64/boot/dts/mediatek/" | grep pinfunc | head
