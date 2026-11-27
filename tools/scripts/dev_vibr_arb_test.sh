#!/bin/sh
echo "=== insmod vibrator ==="
insmod /root/audio/regulator-vibrator.ko
echo "rc=$?"
sleep 0.3
dmesg | grep -iE "regulator_vibrator|vibr_conf|vibrator" | tail -6
ls /sys/class/leds/ 2>/dev/null | head
ls /sys/class/leds/vibrator/ 2>/dev/null

echo
echo "=== i2c arb scan (1,2,5) ==="
insmod /root/audio/i2cscan.ko buses=1,2,5
dmesg | grep i2cscan | grep -E "ACK|done"
rmmod i2cscan
