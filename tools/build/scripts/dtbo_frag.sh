#!/bin/bash
D=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/dtbo/0.dts
for f in 35 36 39 42 43 44; do
    echo "=== fragment@$f ==="
    awk -v pat="fragment@$f \\\\{" '$0 ~ pat {f=1} f {print} f && /^\t\t\};/ {exit}' "$D" | head -40
done
