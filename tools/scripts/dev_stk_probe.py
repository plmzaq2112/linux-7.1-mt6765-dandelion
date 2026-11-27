#!/usr/bin/env python3
"""STK3x1x probe: read chip ID at 0x3E, then enable ALS and read ALS data."""
import ctypes, fcntl, os, sys, time

I2C_RDWR = 0x0707

class Msg(ctypes.Structure):
    _fields_ = [("addr", ctypes.c_uint16), ("flags", ctypes.c_uint16),
                ("len", ctypes.c_uint16), ("buf", ctypes.POINTER(ctypes.c_uint8))]

class Rdwr(ctypes.Structure):
    _fields_ = [("msgs", ctypes.POINTER(Msg)), ("nmsgs", ctypes.c_uint32)]

def xfer(fd, addr, wbytes, rlen, nostop=False):
    wb = (ctypes.c_uint8 * max(1, len(wbytes)))(*wbytes) if wbytes else (ctypes.c_uint8 * 1)()
    rb = (ctypes.c_uint8 * max(1, rlen))()
    msgs = []
    if wbytes:
        msgs.append(Msg(addr, 0, len(wbytes), ctypes.cast(wb, ctypes.POINTER(ctypes.c_uint8))))
    if rlen:
        msgs.append(Msg(addr, 1, rlen, ctypes.cast(rb, ctypes.POINTER(ctypes.c_uint8))))
    arr = (Msg * len(msgs))(*msgs)
    d = Rdwr(ctypes.cast(arr, ctypes.POINTER(Msg)), len(msgs))
    fcntl.ioctl(fd, I2C_RDWR, d)
    return list(rb)

def rd(fd, addr, reg, n=1):
    return xfer(fd, addr, [reg], n)

def wr(fd, addr, reg, val):
    xfer(fd, addr, [reg, val], 0)

bus = int(sys.argv[1]); addr = int(sys.argv[2], 0)
fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)

print("chip id (0x3E) = 0x%02x" % rd(fd, addr, 0x3E)[0])
print("state (0x00) = 0x%02x" % rd(fd, addr, 0x00)[0])

wr(fd, addr, 0x00, 0x02)   # EN_ALS
time.sleep(0.4)
print("state after enable = 0x%02x" % rd(fd, addr, 0x00)[0])
for i in range(8):
    d = rd(fd, addr, 0x13, 2)
    print("als = 0x%02x%02x (%d)" % (d[0], d[1], (d[0] << 8) | d[1]))
    time.sleep(0.35)
os.close(fd)
