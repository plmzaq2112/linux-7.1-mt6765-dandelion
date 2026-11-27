#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
F="$T/drivers/i2c/busses/i2c-mt65xx.c"
echo "=== reg field defines ==="
sed -n '20,70p' "$F"
echo
echo "=== dump_info / debug prints ==="
sed -n '950,1000p' "$F"
