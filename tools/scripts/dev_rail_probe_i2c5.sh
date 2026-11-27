#!/bin/sh
cd /root/audio || exit 1

probe34() {
python3 - <<'PY'
import fcntl, os
try:
    fd=os.open("/dev/i2c-5", os.O_RDWR)
    fcntl.ioctl(fd, 0x0703, 0x34)
    os.write(fd, bytes([0x00]))
    d=os.read(fd,1)
    print("  0x34 ACK reg0=0x%02x" % d[0])
    os.close(fd)
except OSError as e:
    print("  0x34 NAK:", e)
PY
}

for n in ldo-vcn18 ldo-vcn28 ldo-vcamio18 ldo-vaux18 ldo-vio18 ldo-vldo28 ldo-vcamd; do
    insmod regen.ko reg_name="$n" 2>/dev/null
    sleep 0.4
    echo "== $n"
    dmesg | grep "regen:" | tail -1
    probe34
    rmmod regen 2>/dev/null
    sleep 0.2
done
