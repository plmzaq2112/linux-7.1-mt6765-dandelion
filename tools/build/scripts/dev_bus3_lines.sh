#!/bin/sh
echo "=== i2c driver names ==="
ls /sys/bus/platform/drivers/ | grep -i i2c
echo
echo "=== gpio base ==="
cat /sys/class/gpio/gpiochip*/base /sys/class/gpio/gpiochip*/ngpio 2>/dev/null
echo
echo "=== try line state on bus3 (pins 50/51) ==="
D=$(ls /sys/bus/platform/drivers/ | grep -i 'i2c' | head -1)
echo "driver: $D"
echo 1100f000.i2c > /sys/bus/platform/drivers/$D/unbind 2>&1 && echo unbound
sleep 0.3
for g in 50 51; do
    echo $g > /sys/class/gpio/export 2>/dev/null
    echo in > /sys/class/gpio/gpio$g/direction 2>/dev/null
    echo "gpio$g = $(cat /sys/class/gpio/gpio$g/value 2>/dev/null)"
done
for g in 50 51; do echo $g > /sys/class/gpio/unexport 2>/dev/null; done
echo 1100f000.i2c > /sys/bus/platform/drivers/$D/bind 2>&1 && echo rebound
