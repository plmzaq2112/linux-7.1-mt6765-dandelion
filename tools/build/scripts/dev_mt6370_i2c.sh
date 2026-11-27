#!/bin/sh
echo "=== probe 0x34 (bus5) ==="
python3 - <<'PY'
import fcntl, os
bus=5
addr=0x34
try:
    fd=os.open(f"/dev/i2c-{bus}", os.O_RDWR)
    fcntl.ioctl(fd, 0x0703, addr)
    for reg in (0x00, 0x01, 0x02):
        try:
            os.write(fd, bytes([reg]))
            d=os.read(fd, 1)
            print(f"reg 0x{reg:02x} = 0x{d[0]:02x}")
        except OSError as e:
            print(f"reg 0x{reg:02x} NAK/err: {e}")
    os.close(fd)
except Exception as e:
    print("open/bus error:", e)
PY
echo
echo "=== supplier files ==="
cat /sys/bus/i2c/devices/5-0034/waiting_for_supplier 2>/dev/null
ls -l /sys/bus/i2c/devices/5-0034/supplier:* 2>/dev/null
for s in /sys/bus/i2c/devices/5-0034/supplier:*; do readlink -f "$s"; done 2>/dev/null
echo
echo "=== vusb33 regulator ==="
for r in /sys/class/regulator/*; do n=$(cat $r/name 2>/dev/null); case "$n" in *vusb*) echo "$n state=$(cat $r/state)";; esac; done
