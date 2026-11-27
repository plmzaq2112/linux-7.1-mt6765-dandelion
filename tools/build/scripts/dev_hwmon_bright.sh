#!/bin/sh
for h in /sys/class/hwmon/hwmon*; do
    [ -e "$h" ] || continue
    echo "== $h $(cat "$h/name" 2>/dev/null)"
    ls "$h" | head -15
done
echo
B=/sys/class/backlight/panel-backlight
for v in 255 8 120; do
    echo "$v" > $B/brightness
    sleep 2
    echo "brightness=$v"
    for h in /sys/class/hwmon/hwmon*; do
        [ -f "$h/curr1_input" ] && echo "  $(cat $h/name 2>/dev/null) curr1=$(cat $h/curr1_input)"
        [ -f "$h/in1_input" ] && echo "  $(cat $h/name 2>/dev/null) in1=$(cat $h/in1_input)"
    done
done
