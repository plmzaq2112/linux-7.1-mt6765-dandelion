#!/bin/sh
echo "=== pwm ==="
cat /sys/kernel/debug/pwm 2>/dev/null | head -10
echo
echo "=== pin43 mux ==="
grep -E "pin 43|GPIO 43" /sys/kernel/debug/pinctrl/*/pinmux-pins 2>/dev/null | head -3
echo
B=/sys/class/backlight/backlight
echo "max=$(cat $B/max_brightness) cur=$(cat $B/brightness)"
echo 20 > $B/brightness; sleep 0.3
echo "--- after 20 ---"; cat /sys/kernel/debug/pwm | sed -n '2,4p'
echo 80 > $B/brightness; sleep 0.3
echo "--- after 80 ---"; cat /sys/kernel/debug/pwm | sed -n '2,4p'
