#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"

echo "=== vendor disp pwm / leds drivers ==="
find "$V/drivers" -maxdepth 5 \( -iname "*disp_pwm*" -o -iname "*leds-mtk*" -o -iname "*mtk_leds*" \) 2>/dev/null | head -15
echo
echo "=== vendor pwm pinmux refs ==="
grep -rnE "pinmux|GPIO.*PWM|DISP_PWM|PWM0" "$V/drivers/misc/mediatek/leds/" 2>/dev/null | head -20
echo
echo "=== vendor disp_pwm driver ==="
for f in $(find "$V/drivers" -iname "*disp_pwm*.c" 2>/dev/null | head -3); do
    echo "--- ${f#$V/}"
    grep -nE "pinmux|pinctrl|gpio|DISP_PWM|GPIO" "$f" | head -15
done
echo
echo "=== vendor leds dir ==="
ls "$V/drivers/misc/mediatek/leds/" 2>/dev/null | head
