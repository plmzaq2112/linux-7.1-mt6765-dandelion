#!/bin/sh
# dandelion (MT6762G) mainline 7.1 - r6 init
# Changes vs r5:
#   - gadget now exposes ACM + RNDIS in one config (plus MS OS descriptors so
#     Windows binds its RNDIS driver), giving us a network link over USB
#   - usb0 = 192.168.42.1/24, udhcpd hands out 192.168.42.2+ (no admin needed
#     on the Windows side), telnetd listens on port 23
#   - serial shell logic unchanged: ttyGS0 stays silent until the host talks
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

hostname dandelion 2>/dev/null

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
	echo "ACM+RNDIS" > "$G/configs/c.1/strings/0x409/configuration"
	echo 500 > "$G/configs/c.1/MaxPower" 2>/dev/null

	mkdir -p "$G/functions/acm.usb0" 2>/dev/null
	mkdir -p "$G/functions/rndis.usb0" 2>/dev/null
	echo 02:1d:6b:01:04:01 > "$G/functions/rndis.usb0/dev_addr" 2>/dev/null
	echo 02:1d:6b:01:04:02 > "$G/functions/rndis.usb0/host_addr" 2>/dev/null

	# Microsoft OS descriptors: tell Windows this interface is RNDIS
	mkdir -p "$G/os_desc" 2>/dev/null
	echo 1 > "$G/os_desc/use" 2>/dev/null
	echo 0xcd > "$G/os_desc/b_vendor_code" 2>/dev/null
	echo MSFT100 > "$G/os_desc/qw_sign" 2>/dev/null
	mkdir -p "$G/functions/rndis.usb0/os_desc/interface.rndis" 2>/dev/null
	echo RNDIS > "$G/functions/rndis.usb0/os_desc/interface.rndis/compatible_id" 2>/dev/null
	echo 5162001 > "$G/functions/rndis.usb0/os_desc/interface.rndis/sub_compatible_id" 2>/dev/null

	ln -sf "$G/functions/acm.usb0" "$G/configs/c.1/" 2>/dev/null
	ln -sf "$G/functions/rndis.usb0" "$G/configs/c.1/" 2>/dev/null
	ln -sf "$G/configs/c.1" "$G/os_desc" 2>/dev/null
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

net_up() {
	i=0
	while [ ! -d /sys/class/net/usb0 ] && [ "$i" -lt 30 ]; do
		i=$((i + 1))
		sleep 1
	done
	if [ ! -d /sys/class/net/usb0 ]; then
		msg "usb0 netdev MISSING"
		return
	fi
	ifconfig usb0 192.168.42.1 netmask 255.255.255.0 up
	cat > /tmp/udhcpd.conf <<'EOF'
start 192.168.42.2
end 192.168.42.20
interface usb0
opt subnet 255.255.255.0
opt router 192.168.42.1
opt dns 192.168.42.1
opt lease 86400
EOF
	touch /tmp/udhcpd.leases
	udhcpd -S /tmp/udhcpd.leases /tmp/udhcpd.conf
	telnetd -l /bin/sh -p 23
	msg "usb0 192.168.42.1 up, udhcpd + telnetd started"
}
net_up &

serial_loop() {
	while true; do
		if [ ! -c /dev/ttyGS0 ]; then
			sleep 1
			continue
		fi
		exec 3<>/dev/ttyGS0
		msg "ttyGS0 open, staying silent until the host sends a byte"
		dd if=/dev/ttyGS0 bs=1 count=1 of=/dev/null 2>/dev/null
		msg "HOST BYTE OK, spawning shell"
		/bin/sh -i <&3 >&3 2>&3
		msg "shell exited, back to handshake"
		exec 3>&-
		sleep 1
	done
}
serial_loop &

echo
echo "=== dandelion busybox initramfs ready (r6) ==="
echo "kernel: $(uname -a)"
echo "serial: silent until the host presses Enter"
echo "network: usb0 192.168.42.1, telnetd on port 23"
echo

# PID1 must never exit
while true; do
	sleep 3600
done
