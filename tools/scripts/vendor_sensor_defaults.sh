#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
S="$V/drivers/misc/mediatek/sensors-1.0"
echo "=== default i2c_num assignments ==="
grep -rnE "i2c_num *=|i2c_num;" "$S" 2>/dev/null | head -20
echo
echo "=== alsps.c: hw defaults ==="
grep -nE "get_cust_alsps_hw|alsps_hw|i2c_addr" "$S/alsps/alsps.c" | head -15
echo
echo "=== accelhub: any bus ref ==="
grep -rnE "i2c|bus" "$S/accelerometer/accelhub"/*.c 2>/dev/null | head -10
echo
echo "=== scp sensor feature table ==="
sed -n '60,110p' "$V/drivers/misc/mediatek/scp/cm4/scp_feature_table.c"
