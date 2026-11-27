#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== st_accel sc7a20 ==="
grep -n "SC7A20\|sc7a20" "$T/drivers/iio/accel/st_accel.h" "$T/drivers/iio/accel/st_accel_core.c" "$T/drivers/iio/accel/st_accel_i2c.c" | head -20
echo
echo "=== bmc150 bma253 ==="
grep -n "bma253\|BMA253\|BMA250E\|bma250e" "$T/drivers/iio/accel/bmc150-accel-i2c.c" "$T/drivers/iio/accel/bmc150-accel-core.c" | head -15
