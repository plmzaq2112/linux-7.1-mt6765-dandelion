#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
F="$T/drivers/i2c/busses/i2c-mt65xx.c"
echo "=== mainline i2c-mt65xx clk/div handling ==="
grep -nE "clock-div|clock-frequency|clk_get|parent_clk|timing" "$F" | head -30
echo
echo "=== vendor dts i2c props ==="
D=/tmp/v5.dts
dtc -I dtb -O dts -o "$D" /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/dist/phone.fdt 2>/dev/null
for n in 11007000 11008000 11009000 1100f000 11011000 1100d000 11016000; do
    echo "-- i2c@$n"
    awk -v pat="i2c@$n \\\\{" '$0 ~ pat {f=1} f {print} f && /^\t\t\};/ {exit}' "$D" | grep -E "clocks|clock-names|clock-div|clock-frequency|status|compatible|mediatek" | head -8
done
