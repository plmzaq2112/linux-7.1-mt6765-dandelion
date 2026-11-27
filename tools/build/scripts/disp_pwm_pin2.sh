#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"

echo "=== vendor pinctrl DISP_PWM ==="
grep -rniE "disp_pwm|disp pwm" "$V/drivers/pinctrl/" 2>/dev/null | head -15
echo
echo "=== vendor board GPIO43 ==="
grep -rn "GPIO43\|GPIO44" "$V/arch/arm64/boot/dts/mediatek/" 2>/dev/null | head -10
echo
echo "=== mainline pinctrl pwm ==="
grep -rniE "pwm" "$T/drivers/pinctrl/mediatek/pinctrl-mt6765.c" | head -10
echo
echo "=== mainline pinfunc header ==="
ls "$T/arch/arm64/boot/dts/mediatek/" | grep 6765 | head
grep -rn "DISP_PWM" "$T/arch/arm64/boot/dts/mediatek/mt6765-pinfunc.h" 2>/dev/null | head
echo
echo "=== vendor leds-mtk-pwm pinctrl ==="
grep -nE "pinctrl|pinmux|gpio|pwm" "$V/drivers/leds/leds-mtk-pwm.c" | head -20
