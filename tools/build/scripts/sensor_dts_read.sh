#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"
echo "=== sensor_dts.c: what nodes/props ==="
sed -n '1,120p' "$V/drivers/misc/mediatek/sensors-1.0/hwmon/sensor_dts/sensor_dts.c"
