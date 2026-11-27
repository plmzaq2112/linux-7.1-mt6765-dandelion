#!/bin/sh
echo "=== debugfs pwm ==="
cat /sys/kernel/debug/pwm 2>/dev/null | head -30
echo
echo "=== pwmchip0 ==="
ls /sys/class/pwm/pwmchip0 2>/dev/null
for c in /sys/class/pwm/pwmchip0/pwm*; do
    [ -e "$c" ] || continue
    echo "$c period=$(cat $c/period 2>/dev/null) duty=$(cat $c/duty_cycle 2>/dev/null) enable=$(cat $c/enable 2>/dev/null)"
done
echo
echo "=== gpio 154 ==="
cat /sys/kernel/debug/gpio 2>/dev/null | grep -E 'gpio-154|gpio-43' | head -5
echo
echo "=== dmesg pwm/backlight ==="
dmesg | grep -iE 'pwm|backlight|mt6370' | tail -10
echo
echo "=== brightness now ==="
B=/sys/class/backlight/backlight
echo "max=$(cat $B/max_brightness) cur=$(cat $B/brightness)"
