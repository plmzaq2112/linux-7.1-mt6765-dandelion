#!/usr/bin/env python3
"""Register dump using I2C_RDWR (repeated start) — required by many sensors."""
import ctypes, fcntl, os, sys

I2C_RDWR = 0x0707

class Msg(ctypes.Structure):
    _fields_ = [("addr", ctypes.c_uint16),
                ("flags", ctypes.c_uint16),
                ("len", ctypes.c_uint16),
                ("buf", ctypes.POINTER(ctypes.c_uint8))]

class Rdwr(ctypes.Structure):
    _fields_ = [("msgs", ctypes.POINTER(Msg)),
                ("nmsgs", ctypes.c_uint32)]

def read_regs(bus, addr, first, count):
    fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    try:
        res = []
        for reg in range(first, first + count):
            rb = (ctypes.c_uint8 * 1)(reg)
            vb = (ctypes.c_uint8 * 1)()
            m1 = Msg(addr, 0, 1, ctypes.cast(rb, ctypes.POINTER(ctypes.c_uint8)))
            m2 = Msg(addr, 1, 1, ctypes.cast(vb, ctypes.POINTER(ctypes.c_uint8)))
            arr = (Msg * 2)(m1, m2)
            d = Rdwr(ctypes.cast(arr, ctypes.POINTER(Msg)), 2)
            try:
                fcntl.ioctl(fd, I2C_RDWR, d)
                res.append("%02x:%02x" % (reg, vb[0]))
            except OSError as e:
                res.append("%02x:E%d" % (reg, e.errno))
        return " ".join(res)
    finally:
        os.close(fd)

bus = int(sys.argv[1]); addr = int(sys.argv[2], 0)
print(read_regs(bus, addr, 0x00, 0x20))
