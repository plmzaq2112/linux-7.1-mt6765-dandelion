#!/usr/bin/env python3
"""Watch a sensor's registers for changes (light cover / tilt)."""
import ctypes, fcntl, os, sys, time

I2C_RDWR = 0x0707

class Msg(ctypes.Structure):
    _fields_ = [("addr", ctypes.c_uint16), ("flags", ctypes.c_uint16),
                ("len", ctypes.c_uint16), ("buf", ctypes.POINTER(ctypes.c_uint8))]

class Rdwr(ctypes.Structure):
    _fields_ = [("msgs", ctypes.POINTER(Msg)), ("nmsgs", ctypes.c_uint32)]

def read_block(fd, addr, first, count):
    rb = (ctypes.c_uint8 * 1)(first)
    vb = (ctypes.c_uint8 * count)()
    m1 = Msg(addr, 0, 1, ctypes.cast(rb, ctypes.POINTER(ctypes.c_uint8)))
    m2 = Msg(addr, 1, count, ctypes.cast(vb, ctypes.POINTER(ctypes.c_uint8)))
    arr = (Msg * 2)(m1, m2)
    d = Rdwr(ctypes.cast(arr, ctypes.POINTER(Msg)), 2)
    fcntl.ioctl(fd, I2C_RDWR, d)
    return list(vb)

bus = int(sys.argv[1]); addr = int(sys.argv[2], 0)
first = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x00
count = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x20

fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
prev = None
t0 = time.time()
changes = 0
while time.time() - t0 < 12:
    try:
        cur = read_block(fd, addr, first, count)
    except OSError as e:
        print("read err", e); break
    if prev is not None:
        for i, (a, b) in enumerate(zip(prev, cur)):
            if a != b:
                print("%.1fs reg 0x%02x: 0x%02x -> 0x%02x" % (time.time() - t0, first + i, a, b), flush=True)
                changes += 1
    prev = cur
    time.sleep(0.15)
os.close(fd)
print("changes:", changes)
