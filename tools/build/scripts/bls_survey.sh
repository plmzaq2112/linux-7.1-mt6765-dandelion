#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"

echo "=== disp_bls_set_backlight definition ==="
grep -rn "disp_bls_set_backlight" "$V/drivers" "$V/include" 2>/dev/null | head -10

echo
echo "=== BLS registers/driver ==="
grep -rln "DISP_BLS\|disp_bls" "$V/drivers" 2>/dev/null | head -10

echo
echo "=== pin around DISP_PWM ==="
sed -n '525,555p' "$V/drivers/pinctrl/mediatek/pinctrl-mtk-mt6765.h"

echo
echo "=== vendor cust lcd-backlight led node ==="
sed -n '70,90p' "$V/arch/arm64/boot/dts/mediatek/custom_common.dtsi"
