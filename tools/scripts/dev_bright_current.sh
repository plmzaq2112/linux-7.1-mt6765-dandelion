#!/bin/sh
echo "=== power_supply current attrs ==="
for p in /sys/class/power_supply/*; do
    for a in current_now voltage_now power_now status online; do
        [ -f "$p/$a" ] && echo "$(basename $p)/$a=$(cat $p/$a 2>/dev/null)"
    done
done
echo
B=/sys/class/backlight/panel-backlight
echo "=== current at 255 ==="
echo 255 > $B/brightness; sleep 2
for p in /sys/class/power_supply/*; do [ -f "$p/current_now" ] && echo "$(basename $p)=$(cat $p/current_now)"; done
echo "=== current at 8 ==="
echo 8 > $B/brightness; sleep 2
for p in /sys/class/power_supply/*; do [ -f "$p/current_now" ] && echo "$(basename $p)=$(cat $p/current_now)"; done
echo "=== restore 120 ==="
echo 120 > $B/brightness
