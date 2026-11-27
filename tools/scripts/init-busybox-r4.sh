#!/bin/sh
# dandelion (MT6762G) mainline 7.1 - r4 init
# Changes vs r3:
#   - the r96 DTB /chosen/bootargs used to add "console=ttyGS0"; that made the
#     kernel printk share the ACM tty with the shell and wedged it. r4 uses a
#     patched DTB with that token blanked out.
#   - dump /proc/cmdline and /proc/consoles to ttyGS0 so the host can verify
#     from the serial port alone that ttyGS0 is no longer a console.
BB=/bin/busybox
$BB --install -s /bin 2>/dev/null
$BB --install -s /sbin 2>/dev/null

mount -t proc proc /proc 2>/dev/null
mount -t sysfs sysfs /sys 2>/dev/null
mount -t devtmpfs devtmpfs /dev 2>/dev/null || mount -t tmpfs tmpfs /dev 2>/dev/null
mkdir -p /dev/pts /dev/shm /dev 2>/dev/null
mount -t devpts devpts /dev/pts 2>/dev/null
mount -t tmpfs tmpfs /dev/shm 2>/dev/null
mount -t tmpfs tmpfs /tmp 2>/dev/null

msg() {
	echo "init: $*" > /dev/kmsg 2>/dev/null
	echo "init: $*" > /dev/tty0 2>/dev/null
}

G=/sys/kernel/config/usb_gadget/g1

setup_gadget() {
	mount -t configfs none /sys/kernel/config 2>/dev/null
	[ -d "$G" ] || mkdir -p "$G" 2>/dev/null || return 1
	echo 0x1d6b > "$G/idVendor"
	echo 0x0104 > "$G/idProduct"
	echo 0x0100 > "$G/bcdDevice"
	echo 0x0200 > "$G/bcdUSB"
	mkdir -p "$G/strings/0x409" 2>/dev/null
	echo 0123456789 > "$G/strings/0x409/serialnumber"
	echo OpenCode > "$G/strings/0x409/manufacturer"
	echo dandelion > "$G/strings/0x409/product"
	mkdir -p "$G/configs/c.1/strings/0x409" 2>/dev/null
	echo ACM > "$G/configs/c.1/strings/0x409/configuration"
	mkdir -p "$G/functions/acm.usb0" 2>/dev/null
	ln -sf "$G/functions/acm.usb0" "$G/configs/c.1/" 2>/dev/null
	return 0
}

setup_gadget || msg "gadget setup FAILED"

UDC=""
i=0
while [ "$i" -lt 60 ]; do
	UDC=$(ls /sys/class/udc 2>/dev/null | head -n 1)
	[ -n "$UDC" ] && break
	i=$((i + 1))
	sleep 1
done
msg "udc='$UDC' (waited ${i}s)"

if [ -n "$UDC" ]; then
	j=0
	while [ "$j" -lt 10 ]; do
		if echo "$UDC" > "$G/UDC" 2>/dev/null; then
			msg "gadget bound to $UDC"
			break
		fi
		j=$((j + 1))
		sleep 1
	done
	[ "$j" -ge 10 ] && msg "UDC bind FAILED after ${j} tries"
else
	msg "no UDC found, USB serial unavailable"
fi

sleep 1
if [ -c /dev/ttyGS0 ]; then
	msg "ttyGS0 present, shell will attach"
else
	msg "ttyGS0 MISSING"
fi

# sanity info for the host, written to the ACM port itself
{
	echo
	echo "=== dandelion r4 diagnostic ==="
	echo "cmdline: $(cat /proc/cmdline 2>/dev/null)"
	echo "consoles:"
	cat /proc/consoles 2>/dev/null
	echo "=== end diagnostic ==="
} > /dev/ttyGS0 2>/dev/null

# shell over USB serial, respawn on disconnect
(
	while true; do
		if [ -c /dev/ttyGS0 ]; then
			/bin/sh -i < /dev/ttyGS0 > /dev/ttyGS0 2>&1
		fi
		sleep 1
	done
) &

echo
echo "=== dandelion busybox initramfs ready (r4) ==="
echo "kernel: $(uname -a)"
echo "serial: open the USB CDC-ACM port at 115200 8N1, press Enter for a shell"
echo

# PID1 must never exit
while true; do
	sleep 3600
done
