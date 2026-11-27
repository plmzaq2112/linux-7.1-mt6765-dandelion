#!/bin/sh
DRV=i2c-mt65xx
for entry in "11016000 48 49 ref-i2c5" "11009000 103 104 i2c2" "1100f000 50 51 i2c3" "11011000 105 106 i2c4" "1100d000 161 162 i2c6"; do
    set -- $entry
    dev=$1; p1=$2; p2=$3; name=$4
    echo "== $name ($dev) pins $p1/$p2"
    echo $dev.i2c > /sys/bus/platform/drivers/$DRV/unbind 2>/dev/null
    sleep 0.2
    dmesg -C 2>/dev/null
    insmod /root/audio/i2c_lines.ko pins=$p1,$p2 2>/dev/null
    dmesg | grep i2c_lines
    rmmod i2c_lines 2>/dev/null
    echo $dev.i2c > /sys/bus/platform/drivers/$DRV/bind 2>/dev/null
    sleep 0.2
done
