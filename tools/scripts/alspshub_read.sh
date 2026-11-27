#!/bin/bash
S="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/drivers/misc/mediatek/sensors-1.0/alsps/alspshub"
echo "=== alspshub.h ==="
sed -n '1,80p' "$S/alspshub.h"
echo
echo "=== alspshub.c: sensor defs / i2c addr ==="
grep -nE "i2c|addr|SENSOR|stk|als|ps" "$S/alspshub.c" | head -40
