#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/drivers/leds/regulator-vibrator.c"
echo "lines: $(wc -l < "$V")"
echo
echo "=== includes / registration / API usage ==="
grep -nE "^#include|led_classdev|hrtimer_|of_device_id|module_platform_driver|regulator_|platform_|sysfs|DEVICE_ATTR|input_" "$V" | head -60
