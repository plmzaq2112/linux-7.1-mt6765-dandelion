#!/bin/sh
hostname -F /etc/hostname 2>/dev/null
mount -t proc proc /proc 2>/dev/null
mount -t sysfs sysfs /sys 2>/dev/null
mount -t devtmpfs devtmpfs /dev 2>/dev/null
ifconfig lo 127.0.0.1 up 2>/dev/null
if [ -d /sys/class/net/usb0 ]; then
	ifconfig usb0 192.168.42.1 netmask 255.255.255.0 up
	ip addr add 169.254.42.45/16 dev usb0 2>/dev/null
	[ -x /usr/sbin/dropbear ] && dropbear -R -p 22
fi
if [ -b /dev/mmcblk1p1 ]; then
	mkdir -p /mnt/sd
	mount -t vfat /dev/mmcblk1p1 /mnt/sd 2>/dev/null
fi
if [ -x /usr/local/bin/display-start.sh ]; then
	nohup /usr/local/bin/display-start.sh >/var/log/display.log 2>&1 &
fi
exit 0
