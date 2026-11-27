#!/bin/bash
S="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/drivers/misc/mediatek/sensors-1.0"
echo "=== cust_alsps.h ==="
sed -n '1,80p' "$S/alsps/inc/cust_alsps.h"
echo
echo "=== alspshub dir ==="
ls -R "$S/alsps/alspshub" | head -30
echo
echo "=== alsps Kconfig ==="
sed -n '1,60p' "$S/alsps/Kconfig"
