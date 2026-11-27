#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"

echo "=== vendor mt6765 pinctrl files ==="
ls "$V/drivers/pinctrl/mediatek/" | grep -i 6765
echo
echo "=== vendor pin table PWM funcs ==="
for f in $(ls "$V/drivers/pinctrl/mediatek/" | grep -i 6765); do
    echo "--- $f"
    grep -n "PWM" "$V/drivers/pinctrl/mediatek/$f" | head -15
done
echo
echo "=== mainline mt6765 pin table PWM ==="
ls "$T/drivers/pinctrl/mediatek/" | grep -i 6765
grep -n "PWM\|pwm" "$T/drivers/pinctrl/mediatek/pinctrl-mt6765.c" | head -15
echo
echo "=== vendor mtk_leds pwm pin ==="
grep -nE "pwm|PWM|gpio|GPIO|pin" "$V/drivers/misc/mediatek/leds/mt6765/mtk_leds.c" | head -30
