#!/bin/sh
B=/sys/class/backlight/backlight
for v in 88 60 40 25 15 10 6; do
    echo "$v" > $B/brightness
    sleep 1.2
    duty=$(cat /sys/kernel/debug/pwm | grep "actual configuration" | head -1)
    echo "brightness=$v  $duty"
done
echo 44 > $B/brightness
