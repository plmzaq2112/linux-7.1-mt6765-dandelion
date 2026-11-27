#!/bin/sh
echo "=== gpio 154 / 43 ==="
cat /sys/kernel/debug/gpio | grep -E "gpio-154|gpio-43" | head -4
echo
echo "=== pwm ==="
cat /sys/kernel/debug/pwm | sed -n '1,6p'
echo
echo "=== dmesg pwm/backlight ==="
dmesg | grep -iE "pwm-backlight|backlight|pwm" | tail -10
echo
B=/sys/class/backlight/backlight
for v in 0 88; do
    echo "$v" > $B/brightness
    sleep 1
    echo "--- brightness $v"
    cat /sys/kernel/debug/pwm | sed -n '2,4p'
done
echo 44 > $B/brightness
