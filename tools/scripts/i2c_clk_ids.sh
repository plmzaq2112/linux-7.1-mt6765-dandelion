#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== mt6765 clock dt-bindings: I2C ==="
grep -nE "I2C|i2c" "$T/include/dt-bindings/clock/mediatek,mt6765-clk.h" 2>/dev/null | head -20
ls "$T/include/dt-bindings/clock/" | grep -i 6765
echo
echo "=== clk driver i2c gates ==="
grep -nE "i2c" "$T/drivers/clk/mediatek/clk-mt6765.c" 2>/dev/null | head -20
echo
echo "=== i2c driver clock names ==="
grep -nE "devm_clk_get|clock-names|\"main\"|\"dma\"|of_property_read" "$T/drivers/i2c/busses/i2c-mt65xx.c" | head -20
