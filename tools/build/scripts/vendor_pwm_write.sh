#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"

echo "=== vendor set_backlight_cmdq ==="
sed -n '555,600p' "$V/drivers/misc/mediatek/video/common/pwm10/ddp_pwm.c"
echo
echo "=== offset definitions ==="
grep -rn "define DISP_PWM_EN_OFF\|define DISP_PWM_CON_0_OFF\|define DISP_PWM_CON_1_OFF\|define DISP_PWM_DEBUG" "$V/drivers/misc/mediatek/video/" 2>/dev/null | head -10
echo
echo "=== vendor pwm_div/cust_led ==="
grep -n "disp_pwm_get_cust_led" -A30 "$V/drivers/misc/mediatek/video/common/pwm10/ddp_pwm.c" | head -40
