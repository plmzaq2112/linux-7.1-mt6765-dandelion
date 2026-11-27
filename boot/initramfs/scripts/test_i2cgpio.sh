#!/bin/sh
insmod /root/audio/i2c-algo-bit.ko 2>/dev/null
insmod /root/audio/i2c-gpio.ko 2>/dev/null
echo 1100f000.i2c > /sys/bus/platform/drivers/i2c-mt65xx/unbind 2>/dev/null
insmod /root/audio/i2cgpio_dev.ko
sleep 1
dmesg | tail -6
echo "--- buses ---"
ls /dev/i2c-*
echo "--- probe 0x34 ---"
for b in 0 1 2 3 4 5 6 7 8 9; do
    [ -e "/dev/i2c-$b" ] && timeout 3 python3 /root/audio/i2c_probe.py "$b" 0x34
done
