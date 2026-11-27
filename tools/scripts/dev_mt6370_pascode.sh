#!/bin/sh
python3 - <<'PY'
import fcntl, os, time
bus, addr = 5, 0x34
fd = os.open(f"/dev/i2c-{bus}", os.O_RDWR)
fcntl.ioctl(fd, 0x0703, addr)

def wr(reg, val):
    try:
        os.write(fd, bytes([reg, val]))
        return "ok"
    except OSError as e:
        return f"err {e}"

def rd(reg):
    try:
        os.write(fd, bytes([reg]))
        d = os.read(fd, 1)
        return f"0x{d[0]:02x}"
    except OSError as e:
        return f"err {e}"

print("before:")
for r in (0x00, 0x01, 0x02, 0xA9, 0x96):
    print(f"  rd 0x{r:02x}: {rd(r)}")
print("try pas-code writes:")
for reg, val in ((0xE0, 0xA9), (0xE1, 0x96), (0xE2, 0xA9), (0xE3, 0x96)):
    print(f"  wr 0x{reg:02x}=0x{val:02x}: {wr(reg,val)}")
time.sleep(0.05)
print("after:")
for r in (0x00, 0x01, 0x02):
    print(f"  rd 0x{r:02x}: {rd(r)}")
os.close(fd)
PY
