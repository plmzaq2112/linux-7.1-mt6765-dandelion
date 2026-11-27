#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"

echo "=== vendor pin 154 functions ==="
grep -n "MTK_PIN(\s*154" -A14 "$V/drivers/pinctrl/mediatek/pinctrl-mtk-mt6765.h" | head -20
echo
echo "=== vendor pin 43 functions (DISP_PWM) ==="
grep -n "MTK_PIN(\s*43" -A10 "$V/drivers/pinctrl/mediatek/pinctrl-mtk-mt6765.h" | head -14

echo
echo "=== vendor LED mode enum ==="
grep -rn "MT65XX_LED_MODE" "$V/drivers/misc/mediatek/leds/mtk_leds_drv.h" | head -15

echo
echo "=== mainline pwm-mtk-disp registers ==="
grep -nE "define DISP_PWM|EN|CON|WIDTH|THRESH|enabled" "$T/drivers/pwm/pwm-mtk-disp.c" | head -25

echo
echo "=== vendor ddp_pwm registers/enable ==="
grep -nE "define DISP_PWM|_EN|CON|WIDTH|CON0|CON1" "$V/drivers/misc/mediatek/video/common/pwm10/ddp_pwm.c" | head -30
