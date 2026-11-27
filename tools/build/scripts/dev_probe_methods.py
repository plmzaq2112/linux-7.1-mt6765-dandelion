#!/usr/bin/env python3
"""Test different ACK probe methods against known devices on i2c-5."""
import ctypes, fcntl, os

I2C_SLAVE = 0x0703
I2C_RDWR = 0x0707

class Msg(ctypes.Structure):
    _fields_ = [("addr", ctypes.c_uint16),
                ("flags", ctypes.c_uint16),
                ("len", ctypes.c_uint16),
                ("buf", ctypes.POINTER(ctypes.c_uint8))]

class Rdwr(ctypes.Structure):
    _fields_ = [("msgs", ctypes.POINTER(Msg)),
                ("nmsgs", ctypes.c_uint32)]

def probe_len0(bus, addr):
    try:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    except OSError as e:
        return "nodev"
    try:
        buf = (ctypes.c_uint8 * 1)()
        m = Msg(addr, 0, 0, ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint8)))
        d = Rdwr(ctypes.pointer(m), 1)
        fcntl.ioctl(fd, I2C_RDWR, d)
        return "ACK"
    except OSError as e:
        return "NAK(%s)" % e.errno
    finally:
        os.close(fd)

def probe_write1(bus, addr, val=0x00):
    try:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    except OSError:
        return "nodev"
    try:
        fcntl.ioctl(fd, I2C_SLAVE, addr)
        os.write(fd, bytes([val]))
        return "ACK"
    except OSError as e:
        return "NAK(%s)" % e.errno
    finally:
        os.close(fd)

for bus in (5, 0, 1):
    for addr in (0x6b, 0x1a, 0x34, 0x48, 0x19, 0x18):
        print("bus%d 0x%02x len0=%s write1=%s" %
              (bus, addr, probe_len0(bus, addr), probe_write1(bus, addr)), flush=True)
