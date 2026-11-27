#!/usr/bin/env python3
"""Try control-register combinations to get ALS data non-zero."""
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

for state in (0x01, 0x02, 0x03):
    for ctrl in (0x00, 0x01, 0x03, 0x13, 0x23, 0x33, 0x43, 0x53, 0x63, 0x73):
        try:
            xfer(fd, [0x00, 0x00], 0)
            xfer(fd, [0x02, ctrl], 0)
            xfer(fd, [0x00, state], 0)
            time.sleep(0.5)
            b = xfer(fd, [0x10], 0x0C)
            vals = [b[i] << 8 | b[i + 1] for i in range(0, 8, 2)]
            print("state=0x%02x ctrl=0x%02x reg0x10=%02x ch=%s" % (state, ctrl, b[0], vals), flush=True)
        except OSError as e:
            print("state=0x%02x ctrl=0x%02x ERR %s" % (state, ctrl, e), flush=True)
os.close(fd)
