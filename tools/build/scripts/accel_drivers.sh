#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== mainline sc7a20 ? ==="
grep -rln "sc7a20\|SC7A20" "$T/drivers/iio" 2>/dev/null | head
echo "=== bma2x2 / bma253 ? ==="
grep -rln "bma2x2\|bma253\|BMA253" "$T/drivers/iio" 2>/dev/null | head
echo "=== accel drivers available ==="
ls "$T/drivers/iio/accel" | head -50
echo
echo "=== current accel config ==="
grep -nE "CONFIG_BMA|CONFIG_SC7|CONFIG_LIS3DH|CONFIG_IIO_ST_ACCEL|CONFIG_KXCJK|CONFIG_MXC4005|CONFIG_MMA|CONFIG_BMC150" "$T/out/.config" | head -20
