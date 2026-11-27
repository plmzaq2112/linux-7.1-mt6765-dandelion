#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
F="$T/drivers/pwm/pwm-mtk-disp.c"
echo "=== apply 60-180 ==="
sed -n '60,180p' "$F"
echo
echo "=== data 250-310 ==="
sed -n '250,310p' "$F"
