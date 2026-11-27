#!/bin/bash
D=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/v19/v19.dts
echo "arb count: $(grep -c '"arb"' "$D")"
grep -n -B3 '"arb"' "$D" | head -20
