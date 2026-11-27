#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== mainline stk3310 driver ==="
ls -l "$T/drivers/iio/light/stk3310.c" 2>/dev/null
grep -nE "compatible|stk33" "$T/drivers/iio/light/stk3310.c" 2>/dev/null | head -20
echo
echo "=== Kconfig option ==="
grep -n "STK3310" "$T/drivers/iio/light/Kconfig" | head
echo
echo "=== current config ==="
grep -nE "CONFIG_STK3310|CONFIG_IIO=|CONFIG_IIO_BUFFER|CONFIG_MTK_SCP|CONFIG_RPMSG" "$T/out/.config" 2>/dev/null | head -20
echo
echo "=== iio-sensor-proxy on device? (host check not possible) ==="
grep -rn "stk3310" "$T/drivers/iio/light/Makefile" | head -3
