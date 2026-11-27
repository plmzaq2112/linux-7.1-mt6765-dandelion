#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
echo "=== DEBUGSTAT related defs/uses in vendor tree ==="
grep -rn "DEBUGSTAT" "$V/drivers/i2c" "$V/drivers/misc/mediatek" 2>/dev/null | head -20
echo
echo "=== mtk i2c debug bit masks ==="
grep -rnE "SCL.*0x|SDA.*0x|I2C_DEBUG" "$V/drivers/i2c/busses/i2c-mt65xx.c" | head -20
