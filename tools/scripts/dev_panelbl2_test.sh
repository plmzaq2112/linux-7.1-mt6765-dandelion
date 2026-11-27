#!/bin/sh
B=/sys/class/backlight/panel-backlight
echo "max=$(cat $B/max_brightness) cur=$(cat $B/brightness)"
for v in 20 184 60; do
    echo "$v" > $B/brightness
    sleep 1
    echo "set $v -> cur=$(cat $B/brightness)"
done
echo "--- drag simulation (10 quick writes, only last should land) ---"
for v in 30 45 60 75 90 105 120 135 150 165; do
    echo "$v" > $B/brightness
    sleep 0.03
done
sleep 0.5
echo "cur after drag=$(cat $B/brightness)"
echo 110 > $B/brightness
