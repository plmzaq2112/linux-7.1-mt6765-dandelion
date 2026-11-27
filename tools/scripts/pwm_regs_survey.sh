#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"

echo "=== mainline pwm-mtk-disp compat/data ==="
sed -n '1,60p' "$T/drivers/pwm/pwm-mtk-disp.c"
echo
grep -n "compatible\|enable_mask\|mt6765\|mt8183" "$T/drivers/pwm/pwm-mtk-disp.c" | head -20

echo
echo "=== vendor disp_pwm config_init ==="
sed -n '235,300p' "$V/drivers/misc/mediatek/video/common/pwm10/ddp_pwm.c"

echo
echo "=== vendor DISP_PWM offsets ==="
grep -rn "DISP_PWM_EN_OFF\|DISP_PWM_CON_0_OFF\|DISP_PWM_CON_1_OFF" "$V/drivers/misc/mediatek/video/" | head -10
