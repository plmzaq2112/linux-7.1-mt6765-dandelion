#!/usr/bin/env python3
"""Enable ALS on the STK3x1x and watch registers for light changes."""
import ctypes, fcntl, os, sys, time

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

# gain: ALS range 8 (bits 4:5 of 0x02 = 0b10) + it 100ms (bits 0:3 = 0b0011)
xfer(fd, addr, [0x02, 0x23], 0)
xfer(fd, addr, [0x00, 0x02], 0)   # EN_ALS
time.sleep(0.5)

prev = None
t0 = time.time()
n = 0
while time.time() - t0 < 20:
    cur = xfer(fd, addr, [0x00], 0x20)
    if prev:
        for i, (a, b) in enumerate(zip(prev, cur)):
            if a != b:
                print("%.1fs reg 0x%02x: 0x%02x -> 0x%02x" % (time.time() - t0, i, a, b), flush=True)
                n += 1
    prev = cur
    time.sleep(0.2)
print("changes:", n)
print("regs 0x0d..0x15:", " ".join("%02x" % v for v in prev[0x0d:0x16]))
os.close(fd)
