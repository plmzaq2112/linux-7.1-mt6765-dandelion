#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
echo "=== i2c-gpio module ==="
ls -l "$T/out/drivers/i2c/busses/i2c-gpio.ko" 2>/dev/null && cp "$T/out/drivers/i2c/busses/i2c-gpio.ko" "$W/dist/"
echo
echo "=== disabled hw nodes ==="
D="$W/logs/repack20/new.dts"
for n in 11009000 1100f000 11011000 1100d000; do
    i=$(grep -n "i2c@$n {" "$D" | head -1 | cut -d: -f1)
    echo "-- i2c@$n (line $i)"
    sed -n "${i},$((i+16))p" "$D" | grep -E "status|clocks"
done
