#!/usr/bin/env python3
"""Re-init the ALS from scratch and dump state before/after."""
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

def dump(tag):
    b = xfer(fd, addr, [0x00], 0x20)
    print("%s: %s" % (tag, " ".join("%02x:%02x" % (i, v) for i, v in enumerate(b))), flush=True)

dump("initial")
xfer(fd, addr, [0x00, 0x00], 0); time.sleep(0.15)
xfer(fd, addr, [0x02, 0x23], 0); time.sleep(0.15)
xfer(fd, addr, [0x00, 0x02], 0); time.sleep(1.0)
dump("after-enable")
time.sleep(1.0)
dump("after-1s")
xfer(fd, addr, [0x00, 0x03], 0); time.sleep(1.0)
dump("als+ps")
os.close(fd)
