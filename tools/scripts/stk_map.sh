#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
F="$T/drivers/iio/light/stk3310.c"
echo "=== stk3310 register map ==="
grep -nE "#define STK3310_REG|STATE_|CHIP_ID|STK3310_CHIP" "$F" | head -30
echo
echo "=== channel / data regs ==="
grep -nE "STK3310_REG_ALS|STK3310_REG_PS|als_data|ps_data" "$F" | head -15
