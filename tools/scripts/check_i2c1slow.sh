#!/bin/bash
D=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/repack23/new.dts
echo "=== clock-frequency values in file ==="
grep -n "clock-frequency" "$D" | head -12
echo
echo "=== i2c@11008000 node ==="
i=$(grep -n "i2c@11008000 {" "$D" | head -1 | cut -d: -f1)
sed -n "${i},$((i+20))p" "$D"
