#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
echo "=== vendor debugstat bits ==="
grep -nE "DEBUGSTAT|SDA|SCL" "$V/drivers/i2c/busses/i2c-mt65xx.c" | grep -iE "debugstat|define" | head -20
echo
echo "=== mainline: which regs for mt6765 ==="
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
grep -nE "mt6765|mt8183|mt8173" "$T/drivers/i2c/busses/i2c-mt65xx.c" | head -10
