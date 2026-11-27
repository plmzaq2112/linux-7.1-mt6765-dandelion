#!/bin/sh
cd /root/audio || exit 1

insmod i2c-algo-bit.ko 2>/dev/null
insmod i2c-gpio.ko 2>/dev/null
echo 1100f000.i2c > /sys/bus/platform/drivers/i2c-mt65xx/unbind 2>/dev/null
insmod i2cgpio_dev.ko
insmod ampen.ko 2>/dev/null
sleep 1
echo "=== gpio bus ==="
dmesg | grep "i2c-gpio" | tail -1
python3 i2c_probe.py 3 0x34

for n in ldo-vio28 ldo-vio18 ldo-vcn18 ldo-vcamio18 ldo-vldo28 ldo-vaux18 ldo-vcama ldo-vcamd ldo-vmch ldo-vmc; do
    insmod regen.ko reg_name="$n" 2>/dev/null
    sleep 1
    echo "== $n"
    dmesg | grep "regen:" | tail -1
    timeout 4 python3 i2c_probe.py 3 0x34
    rmmod regen 2>/dev/null
    sleep 1
done
