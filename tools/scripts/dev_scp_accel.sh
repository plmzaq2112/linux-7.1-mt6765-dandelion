#!/bin/sh
dd if=/dev/disk/by-partlabel/scp2 bs=1M status=none 2>/dev/null \
  | tr -c '[:print:]' '\n' > /tmp/scp2.txt
echo "lines: $(wc -l < /tmp/scp2.txt)"
echo "=== accel chip names ==="
grep -ioE 'bma[0-9]{3,4}|bmi[0-9]{3,4}|lis[0-9][a-z0-9]{2,4}|lsm[0-9][a-z0-9]{3,4}|kxtj[0-9]|kxti[0-9]|mc3[0-9]{3}|mxc[0-9]{3,4}|adxl[0-9]{3}|sc7[0-9a-z]{3,4}|icm[0-9]{5}|mpu[0-9]{4}|qma[0-9]{4}|stk3[0-9a-z]+|stk8[0-9a-z]+' /tmp/scp2.txt | sort | uniq -c | sort -rn | head -25
echo
echo "=== sensor init lines ==="
grep -iE "Init|probe" /tmp/scp2.txt | grep -iE "acc|gsensor|bma|bmi|lis|kxt|mc3|mxc|sc7|stk" | sort -u | head -20
echo
echo "=== 'sensor' device names ==="
grep -iE "^[A-Za-z0-9_]+Sensor$|gsensor|accelerometer" /tmp/scp2.txt | sort -u | head -20
