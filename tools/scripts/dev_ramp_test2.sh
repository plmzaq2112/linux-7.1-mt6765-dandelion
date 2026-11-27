#!/bin/sh
systemctl stop alsd 2>/dev/null
for pass in 1 2 3; do
    for v in $(seq 300 50 1600) $(seq 1600 -50 300); do
        echo $v > /sys/class/backlight/panel-backlight/brightness
        sleep 0.12
    done
done
echo ramp-done
