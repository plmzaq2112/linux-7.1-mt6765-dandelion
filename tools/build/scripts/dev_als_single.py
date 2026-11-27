#!/usr/bin/env python3
"""Read registers one by one (no auto-increment quirks) and print as reg=val."""
import ctypes, fcntl, os, sys

I2C_RDWR = 0x0707
class Msg(ctypes.Structure):
    _fields_ = [("addr", ctypes.c_uint16), ("flags", ctypes.c_uint16),
                ("len", ctypes.c_uint16), ("buf", ctypes.POINTER(ctypes.c_uint8))]
class Rdwr(ctypes.Structure):
    _fields_ = [("msgs", ctypes.POINTER(Msg)), ("nmsgs", ctypes.c_uint32)]

def xfer(fd, addr, w, rlen):
    wb = (ctypes.c_uint8 * max(1, len(w)))(*w)
    rb = (ctypes.c_uint8 * max(1, rlen))()
    msgs = [Msg(addr, 0, len(w), ctypes.cast(wb, ctypes.POINTER(ctypes.c_uint8)))]
    if rlen:
        msgs.append(Msg(addr, 1, rlen, ctypes.cast(rb, ctypes.POINTER(ctypes.c_uint8))))
    arr = (Msg * len(msgs))(*msgs)
    d = Rdwr(ctypes.cast(arr, ctypes.POINTER(Msg)), len(msgs))
    fcntl.ioctl(fd, I2C_RDWR, d)
    return list(rb)

bus = int(sys.argv[1]); addr = int(sys.argv[2], 0)
fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
# enable ALS, keep PS off
xfer(fd, addr, [0x00, 0x00], 0)
xfer(fd, addr, [0x01, 0x00], 0)
xfer(fd, addr, [0x02, 0x23], 0)
xfer(fd, addr, [0x00, 0x02], 0)
import time; time.sleep(0.6)
for reg in range(0x00, 0x30):
    v = xfer(fd, addr, [reg], 1)[0]
    print("r%02x=%02x" % (reg, v), end=" ")
    if reg % 8 == 7:
        print()
print()
os.close(fd)
