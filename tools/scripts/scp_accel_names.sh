#!/bin/bash
B=/dev/disk/by-partlabel/scp2
dd if="$B" bs=1M status=none 2>/dev/null | tr -c '[:print:]' '\n' > /tmp/scp2.txt
echo "=== accel / gsensor chip candidates ==="
grep -ioE 'bma[0-9]{3,4}|bmi[0-9]{3,4}|lis[0-9a-z]{2,4}|lsm[0-9a-z]{3,4}|kxtj[0-9]|kxti[0-9]|mc3[0-9]{3}|mxc[0-9]{3,4}|adxl[0-9]{3}|sc7[0-9a-z]{3,4}|da[0-9]{3}|icm[0-9]{5}|mpu[0-9]{4}|qma[0-9]{4}|stk3[0-9a-z]+|stk8[0-9a-z]+' /tmp/scp2.txt | sort | uniq -c | sort -rn | head -25
echo
echo "=== lines with init/probe of sensors ==="
grep -iE "init|probe|detect" /tmp/scp2.txt | grep -iE "acc|gsensor|gyro|mag|bma|bmi|lis|kxt|mc3|mxc|sc7" | sort -u | head -20
