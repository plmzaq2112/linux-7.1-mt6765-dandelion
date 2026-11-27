#!/bin/sh
# Load the AFE module with console output suppressed, to separate a real
# driver hang from a console/fbcon/DRM hang.
echo 0 > /proc/sys/kernel/printk
insmod /root/audio/snd-soc-mt6765-pcm.ko
rc=$?
echo 7 > /proc/sys/kernel/printk
echo "insmod rc=$rc"
sleep 1
dmesg | tail -40
