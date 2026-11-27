#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
F="/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/dist/phone.fdt"
D=/tmp/pio2.dts
dtc -I dtb -O dts -o "$D" "$F" 2>/dev/null

echo "=== pinctrl node ==="
grep -nE "pinctrl@|mediatek,mt6765-pinctrl|#gpio-cells" "$D" | head -10
echo
echo "=== pinctrl node detail ==="
N=$(grep -n "mt6765-pinctrl" "$D" | head -1 | cut -d: -f1)
if [ -n "$N" ]; then sed -n "$((N-5)),$((N+30))p" "$D"; fi
echo
echo "=== encoding macros ==="
grep -rn "MTK_GET_PIN_NO\|MTK_GET_PIN_FUNC" "$T/drivers/pinctrl/mediatek/" 2>/dev/null | head -8
