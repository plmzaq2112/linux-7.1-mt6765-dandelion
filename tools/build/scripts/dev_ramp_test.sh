#!/bin/sh
systemctl stop alsd 2>/dev/null
for pass in 1 2 3; do
    for v in $(seq 400 25 900) $(seq 900 -25 400); do
        echo $v > /sys/class/backlight/panel-backlight/brightness
        sleep 0.06
    done
    sleep 1
done
echo ramp-done
