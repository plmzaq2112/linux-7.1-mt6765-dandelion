#!/bin/sh
hostname -F /etc/hostname 2>/dev/null
mount -t proc proc /proc 2>/dev/null
mount -t sysfs sysfs /sys 2>/dev/null
mount -t devtmpfs devtmpfs /dev 2>/dev/null
ifconfig lo 127.0.0.1 up 2>/dev/null

# --- timezone: Beijing ---
export TZ=CST-8
echo 'CST-8' > /etc/TZ
hwclock -s 2>/dev/null

# --- network ---
if [ -d /sys/class/net/usb0 ]; then
	ifconfig usb0 192.168.42.1 netmask 255.255.255.0 up
	ip addr add 169.254.42.45/16 dev usb0 2>/dev/null
	[ -x /usr/sbin/dropbear ] && dropbear -R -p 22
fi

if [ -b /dev/mmcblk1p1 ]; then
	mkdir -p /mnt/sd
	mount -t vfat /dev/mmcblk1p1 /mnt/sd 2>/dev/null
fi

# --- GUI: seatd + weston + wallpaper ---
mkdir -p /run/user/0
chmod 700 /run/user/0
rm -f /run/user/0/wayland-* 2>/dev/null
[ -x /usr/bin/seatd ] && seatd -g root >/tmp/seatd.log 2>&1 &
sleep 1
export XDG_RUNTIME_DIR=/run/user/0
[ -x /usr/bin/weston ] && weston --backend=drm-backend.so --idle-time=0 \
	--continue-without-input --log=/tmp/weston.log >/tmp/weston.out 2>&1 &
sleep 4
# socket name is usually wayland-0 after clearing stale ones
if [ -S /run/user/0/wayland-0 ]; then
	export WAYLAND_DISPLAY=wayland-0
elif [ -S /run/user/0/wayland-1 ]; then
	export WAYLAND_DISPLAY=wayland-1
fi
[ -x /usr/bin/mpv ] && [ -f /root/wallpaper_opt.mp4 ] && \
	mpv --no-config --fullscreen --loop --no-audio --vo=wlshm \
		/root/wallpaper_opt.mp4 >/tmp/mpv.out 2>&1 &

exit 0
