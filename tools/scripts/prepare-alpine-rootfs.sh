#!/bin/bash
# Build a dandelion-customised Alpine aarch64 rootfs tarball.
#
# The stock alpine-minirootfs has no init system (it is meant for chroot), so we
# add a busybox init + inittab, an rcS that brings up the USB network and
# telnetd, and a serial shell that stays silent until the host sends a byte
# (writing to the ACM tty with no host attached wedges the tty).
set -e

A="/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"/artifacts
S="$HOME/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs-alpine"
SRC="$A/alpine-minirootfs-3.24.4-aarch64.tar.gz"
OUT="$A/dandelion-alpine-3.24.4.tar.gz"

rm -rf "$S"
mkdir -p "$S"
tar -xzf "$SRC" -C "$S" --no-same-owner

# --- base system glue -------------------------------------------------------
ln -sf /bin/busybox "$S/sbin/init"
mkdir -p "$S/etc/init.d" "$S/usr/local/sbin" "$S/var/lib/misc"

cat > "$S/etc/inittab" <<'EOF'
# dandelion: busybox init
::sysinit:/etc/init.d/rcS
::sysinit:/bin/mkdir -p /dev/pts /dev/shm
::sysinit:/bin/mount -t devpts devpts /dev/pts
::sysinit:/bin/mount -t tmpfs tmpfs /dev/shm
ttyGS0::respawn:/usr/local/sbin/serial-shell
tty1::respawn:/sbin/getty 38400 tty1
::ctrlaltdel:/sbin/reboot
::shutdown:/bin/umount -a -r
EOF

cat > "$S/etc/init.d/rcS" <<'EOF'
#!/bin/sh
hostname -F /etc/hostname 2>/dev/null
mount -t proc proc /proc 2>/dev/null
mount -t sysfs sysfs /sys 2>/dev/null
mount -t devtmpfs devtmpfs /dev 2>/dev/null
ifconfig lo 127.0.0.1 up 2>/dev/null

# USB network comes from the initramfs gadget (usb0 already exists)
i=0
while [ ! -d /sys/class/net/usb0 ] && [ "$i" -lt 20 ]; do
	i=$((i + 1))
	sleep 1
done
if [ -d /sys/class/net/usb0 ]; then
	ifconfig usb0 192.168.42.1 netmask 255.255.255.0 up
	mkdir -p /var/lib/misc
	touch /var/lib/misc/udhcpd.leases
	udhcpd -S /var/lib/misc/udhcpd.leases /etc/udhcpd.conf
	telnetd -l /bin/sh -p 23
fi
exit 0
EOF
chmod 0755 "$S/etc/init.d/rcS"

cat > "$S/usr/local/sbin/serial-shell" <<'EOF'
#!/bin/sh
# never write to the ACM tty before the host has sent something
while [ ! -c /dev/ttyGS0 ]; do sleep 1; done
exec 3<>/dev/ttyGS0
dd if=/dev/ttyGS0 bs=1 count=1 of=/dev/null 2>/dev/null
exec /bin/sh -i <&3 >&3 2>&3
EOF
chmod 0755 "$S/usr/local/sbin/serial-shell"

cat > "$S/etc/udhcpd.conf" <<'EOF'
start 192.168.42.2
end 192.168.42.20
interface usb0
opt subnet 255.255.255.0
opt router 192.168.42.1
opt dns 192.168.42.1
opt lease 86400
EOF

cat > "$S/etc/fstab" <<'EOF'
/dev/mmcblk0p40	/	ext4	rw,relatime	0	1
EOF

printf 'dandelion\n' > "$S/etc/hostname"
printf 'nameserver 192.168.42.2\n' > "$S/etc/resolv.conf"

cat > "$S/etc/motd" <<'EOF'

  dandelion (MT6762G) - Alpine Linux (mainline 7.1)
  serial: ttyGS0 / telnet: 192.168.42.1

EOF

mkdir -p "$S/var/lib/misc"

tar -czf "$OUT" -C "$S" --owner=0 --group=0 --numeric-owner .
ls -l "$OUT"
sha256sum "$OUT"
