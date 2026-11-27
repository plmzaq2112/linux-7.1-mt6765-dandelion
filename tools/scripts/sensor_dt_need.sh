#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== stk3310 probe ==="
sed -n '/^static int stk3310_probe/,/^}/p' "$T/drivers/iio/light/stk3310.c" | tail -60
echo
echo "=== st_sensors core supplies ==="
grep -n "devm_regulator_get\|vdd\|vddio" "$T/drivers/iio/common/st_sensors/st_sensors_core.c" | head -12
