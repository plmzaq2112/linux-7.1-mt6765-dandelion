#!/bin/bash
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
D=/tmp/vendor2.dts
dtc -I dtb -O dts -o "$D" "$W/dist/phone.fdt" 2>/dev/null || { echo "dtc failed"; exit 1; }
for n in 11007000 11008000 11009000 1100f000 11011000 1100d000 11016000; do
    echo "=== i2c@$n ==="
    awk -v pat="i2c@$n \\\\{" '$0 ~ pat {f=1} f {print} f && /^\t\t\};/ {exit}' "$D" | grep -E "compatible|^\t\t\t[a-z0-9_@-]+ \{|status" | head -20
done
