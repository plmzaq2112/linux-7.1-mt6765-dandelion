#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
F="$T/drivers/iio/light/stk3310.c"
echo "=== of_match / chip ids ==="
grep -nE "of_device_id|compatible|chip_ids|stk3310_chip_id" -A6 "$F" | sed -n '1,60p'
echo
echo "=== probe: supplies, irq, reset ==="
grep -nE "devm_regulator_get|vdd|vled|reset|irq|devm_iio_device_register|i2c_set_clientdata" "$F" | head -30
