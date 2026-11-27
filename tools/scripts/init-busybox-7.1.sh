#!/bin/sh
# Minimal init: dandelion (MT6762G) mainline 7.1 + BusyBox initramfs.
# Rules learned from the first (failed) boot:
#   - PID1 must never exit: "Attempted to kill init" panics the kernel.
#   - LK asserts if the boot DTB lacks the dtbo overlay symbols (needs r96 DTB).
#   - Consoles: tty0 (fbcon / simple-framebuffer) and ttyGS0 (USB CDC-ACM).

BB=/bin/busybox
$BB --install -s /bin 2>/dev/null
$BB --install -s /sbin 2>/dev/null

mount -t proc proc /proc 2>/dev/null
mount -t sysfs sysfs /sys 2>/dev/null
mount -t devtmpfs devtmpfs /dev 2>/dev/null || mount -t tmpfs tmpfs /dev 2>/dev/null
mkdir -p /dev/pts /dev/shm 2>/dev/null
mount -t devpts devpts /dev/pts 2>/dev/null
mount -t tmpfs tmpfs /dev/shm 2>/dev/null
mount -t tmpfs tmpfs /tmp 2>/dev/null

# ---- USB CDC-ACM gadget: ttyGS0 on device, COMx on host ----
setup_gadget() {
	mount -t configfs none /sys/kernel/config 2>/dev/null
	G=/sys/kernel/config/usb_gadget/g1
	[ -d "$G" ] && return 0
	mkdir -p "$G" 2>/dev/null || return 1
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
	UDC=$(ls /sys/class/udc 2>/dev/null | head -n 1)
	[ -n "$UDC" ] && echo "$UDC" > "$G/UDC"
	return 0
}
setup_gadget

echo
echo "=== dandelion busybox initramfs ready ==="
echo "kernel: $(uname -a)"
echo

# Extra shell over the USB serial console once it exists.
(
	while [ ! -c /dev/ttyGS0 ]; do sleep 1; done
	echo "init: ttyGS0 ready, shell attached (Ctrl-A then q on host to detach)"
	/bin/sh -i < /dev/ttyGS0 > /dev/ttyGS0 2>&1
) &

# Primary shell uses the kernel console handed to PID1 (fbcon tty0 if available).
while true; do
	/bin/sh -i
	echo "init: shell exited, respawning in 1s (kernel stays alive)"
	sleep 1
done
