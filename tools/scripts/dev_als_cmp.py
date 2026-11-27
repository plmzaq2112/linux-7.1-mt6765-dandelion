#!/usr/bin/env python3
"""Compare block-read vs single-register read for the ALS data registers."""
import ctypes, fcntl, os, time

I2C_RDWR = 0x0707
BUS, ADDR = 8, 0x47

class Msg(ctypes.Structure):
    _fields_ = [("addr", ctypes.c_uint16), ("flags", ctypes.c_uint16),
                ("len", ctypes.c_uint16), ("buf", ctypes.POINTER(ctypes.c_uint8))]
class Rdwr(ctypes.Structure):
    _fields_ = [("msgs", ctypes.POINTER(Msg)), ("nmsgs", ctypes.c_uint32)]

def xfer(fd, w, rlen):
    wb = (ctypes.c_uint8 * max(1, len(w)))(*w)
    rb = (ctypes.c_uint8 * max(1, rlen))()
    msgs = [Msg(ADDR, 0, len(w), ctypes.cast(wb, ctypes.POINTER(ctypes.c_uint8)))]
    if rlen:
        msgs.append(Msg(ADDR, 1, rlen, ctypes.cast(rb, ctypes.POINTER(ctypes.c_uint8))))
    arr = (Msg * len(msgs))(*msgs)
    d = Rdwr(ctypes.cast(arr, ctypes.POINTER(Msg)), len(msgs))
    fcntl.ioctl(fd, I2C_RDWR, d)
    return list(rb)

fd = os.open("/dev/i2c-%d" % BUS, os.O_RDWR)
xfer(fd, [0x00, 0x02], 0)
xfer(fd, [0x02, 0x23], 0)
time.sleep(0.5)
for i in range(6):
    b = xfer(fd, [0x00], 0x20)
    print("block : r10=%02x r12=%02x r13=%02x r14=%02x r15=%02x r16=%02x r18=%02x r1a=%02x"
          % (b[0x10], b[0x12], b[0x13], b[0x14], b[0x15], b[0x16], b[0x18], b[0x1a]), flush=True)
    for r in (0x10, 0x12, 0x13, 0x14, 0x15):
        v = xfer(fd, [r], 1)[0]
        print("single: r%02x=%02x" % (r, v), end="  ")
    print()
    time.sleep(0.5)
os.close(fd)
