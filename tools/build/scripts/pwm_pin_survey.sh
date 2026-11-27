#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
F="/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/dist/phone.fdt"
D=/tmp/pwmpin.dts
dtc -I dtb -O dts -o "$D" "$F" 2>/dev/null

echo "=== running dtb disp_pwm/pwm pinctrl ==="
grep -n 'pwm@1100e000' -B5 -A30 "$D" | head -45
echo
echo "=== vendor dts disp_pwm / pwm pin ==="
grep -rniE "disp_pwm|DISP_PWM|pwm" "$V/arch/arm64/boot/dts/mediatek/dandelion/" "$V/arch/arm64/boot/dts/mediatek/custom_common.dtsi" 2>/dev/null | head -25
echo
echo "=== mt6765 pinfunc DISP_PWM ==="
grep -rn "DISP_PWM" "$T/arch/arm64/boot/dts/mediatek/" "$T/drivers/pinctrl/mediatek/pinctrl-mt6765.c" 2>/dev/null | head -10
echo
echo "=== mainline pwm driver pinctrl? ==="
grep -n "pinctrl\|of_property" "$T/drivers/pwm/pwm-mtk-disp.c" | head -10
