#!/bin/sh
B=/sys/class/backlight/backlight
echo "max=$(cat $B/max_brightness) cur=$(cat $B/brightness)"
for v in 10 40 80; do
    echo "$v" > $B/brightness
    sleep 0.4
    echo "--- $v"
    cat /sys/kernel/debug/pwm | sed -n '2,4p'
done
echo "--- restore 44 ---"
echo 44 > $B/brightness
echo "cur=$(cat $B/brightness)"
