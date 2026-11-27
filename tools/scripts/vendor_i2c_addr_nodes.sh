#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
echo "=== files with i2c_addr ==="
grep -rln "i2c_addr" "$V/arch/arm64/boot/dts" 2>/dev/null | head -20
echo
echo "=== occurrences ==="
grep -rn -B6 "i2c_addr" "$V/arch/arm64/boot/dts" 2>/dev/null | grep -E "i2c_num|i2c_addr|@|compatible|alsps|accel|gsensor" | head -40
