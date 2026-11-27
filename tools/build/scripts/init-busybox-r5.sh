#!/bin/sh
# dandelion (MT6762G) mainline 7.1 - r5 init
# Changes vs r4:
#   - nothing is written to /dev/ttyGS0 until the host sends a byte, so a
#     missing host can never wedge the ACM tty
#   - after the handshake byte, a 100 KiB bulk TX test runs with markers on
#     tty0: if the screen shows "tx test done" but the host sees few bytes the
#     data is lost after the controller; if the marker never appears the tty
#     write itself is stuck
#   - only then the interactive shell is spawned on the same tty
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

serial_loop() {
	while true; do
		if [ ! -c /dev/ttyGS0 ]; then
			sleep 1
			continue
		fi
		exec 3<>/dev/ttyGS0
		msg "ttyGS0 open, staying silent until the host sends a byte"
		dd if=/dev/ttyGS0 bs=1 count=1 of=/dev/null 2>/dev/null
		msg "HOST BYTE OK"
		msg "tx test start: 100 KiB of Z"
		dd if=/dev/zero bs=1024 count=100 2>/dev/null | tr '\0' 'Z' > /dev/ttyGS0
		msg "tx test done"
		msg "spawning shell"
		/bin/sh -i <&3 >&3 2>&3
		msg "shell exited, back to handshake"
		exec 3>&-
		sleep 1
	done
}
serial_loop &

echo
echo "=== dandelion busybox initramfs ready (r5) ==="
echo "kernel: $(uname -a)"
echo "serial: silent until the host presses Enter, then 100 KiB tx test"
echo

# PID1 must never exit
while true; do
	sleep 3600
done
