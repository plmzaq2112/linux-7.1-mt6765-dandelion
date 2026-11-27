#!/bin/bash
D=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/dtbo/0.dts
echo "=== sensor-ish nodes ==="
grep -nE "alsps|stk3|sensor|light|accel|gsensor|board-sensor|VIRTUAL" "$D" | head -30
echo
echo "=== i2c node overrides ==="
grep -nE "i2c[0-9]|i2c@" "$D" | head -25
echo
echo "=== fragment count ==="
grep -cE "fragment@" "$D"
