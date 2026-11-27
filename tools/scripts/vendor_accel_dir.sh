#!/bin/bash
S="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/drivers/misc/mediatek/sensors-1.0"
echo "=== accelerometer dir ==="
ls "$S/accelerometer" 2>/dev/null | head -20
echo
echo "=== hwmon dir (sensor hub generic) ==="
ls "$S/hwmon" 2>/dev/null | head -20
echo
echo "=== sensorHub dir ==="
ls "$S/sensorHub" 2>/dev/null | head -20
echo
echo "=== any cust_acc / i2c_num in sensors-1.0 ==="
grep -rn "i2c_num" "$S" 2>/dev/null | head -10
