#!/bin/sh
B=/sys/class/backlight/panel-backlight
echo 120 > $B/brightness 2>/dev/null

P=/sys/class/pwm/pwmchip0
echo 0 > $P/export 2>/dev/null
sleep 0.3
echo 39385 > $P/pwm0/period
echo 30000 > $P/pwm0/duty_cycle
echo 1 > $P/pwm0/enable
sleep 0.8
echo "=== duty 30000 ==="
cat /sys/kernel/debug/pwm | sed -n '2,5p'

echo 3000 > $P/pwm0/duty_cycle
sleep 1
echo "=== duty 3000 ==="
cat /sys/kernel/debug/pwm | sed -n '2,5p'

echo 35000 > $P/pwm0/duty_cycle
sleep 1
echo "=== duty 35000 ==="
cat /sys/kernel/debug/pwm | sed -n '2,5p'
