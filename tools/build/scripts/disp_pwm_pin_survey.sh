#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"

echo "=== vendor DISP_PWM pinmux ==="
grep -rn "DISP_PWM" "$V/arch/arm64/boot/dts/mediatek/" 2>/dev/null | head -20
echo
echo "=== vendor pinfunc DISP_PWM ==="
grep -rn "DISP_PWM" "$V/arch/arm64/boot/dts/mediatek/mt6765-pinfunc.h" 2>/dev/null | head -10
echo
echo "=== mainline pinfunc DISP_PWM ==="
grep -rn "DISP_PWM" "$T/arch/arm64/boot/dts/mediatek/mt6765-pinfunc.h" 2>/dev/null | head -10
echo
echo "=== vendor disp_pwm node ==="
grep -n "disp_pwm" -A20 "$V/arch/arm64/boot/dts/mediatek/mt6765.dts" | head -30
echo
echo "=== panel backlight gpio in running dtb ==="
grep -n "ft8006s\|fitipower\|backlight-gpios" -B5 -A15 /tmp/pwmpin.dts 2>/dev/null | head -40
