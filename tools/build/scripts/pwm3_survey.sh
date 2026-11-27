#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"

echo "=== vendor lcd-backlight led node ==="
grep -n "led@6\|lcd-backlight" -A12 "$V/arch/arm64/boot/dts/mediatek/mt6765.dts" | head -20

echo
echo "=== vendor mtk_leds parse pwm_config ==="
sed -n '190,250p' "$V/drivers/misc/mediatek/leds/mt6765/mtk_leds.c"

echo
echo "=== vendor pin table around PWM3 ==="
sed -n '1160,1210p' "$V/drivers/pinctrl/mediatek/pinctrl-mtk-mt6765.h"

echo
echo "=== mainline pwm@11006000 node ==="
F="/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/dist/phone.fdt"
D=/tmp/pwm3.dts
dtc -I dtb -O dts -o "$D" "$F" 2>/dev/null
grep -n 'pwm@11006000' -A20 "$D" | head -30
