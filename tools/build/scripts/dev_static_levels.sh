#!/bin/sh
B=/sys/class/backlight/panel-backlight/brightness
for v in 300 800 1500; do
    echo $v > $B
    echo "level $v hold"
    sleep 6
done
echo static-done
