#!/bin/sh
B=/sys/class/backlight/panel-backlight
echo "max=$(cat $B/max_brightness) cur=$(cat $B/brightness)"
for v in 120 1472 480; do
    echo "$v" > $B/brightness
    sleep 1.5
    echo "set $v -> cur=$(cat $B/brightness)"
done
