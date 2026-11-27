#!/bin/sh
B=/sys/class/backlight/panel-backlight
echo "max=$(cat $B/max_brightness) cur=$(cat $B/brightness)"
echo "--- gpio154 ---"
cat /sys/kernel/debug/gpio | grep -E "gpio-154" | head -2
echo "--- set 30 ---"
echo 30 > $B/brightness; sleep 0.8
echo "cur=$(cat $B/brightness)"
echo "--- set 200 ---"
echo 200 > $B/brightness; sleep 0.8
echo "cur=$(cat $B/brightness)"
echo "--- set 80 ---"
echo 80 > $B/brightness; sleep 0.8
echo "cur=$(cat $B/brightness)"
