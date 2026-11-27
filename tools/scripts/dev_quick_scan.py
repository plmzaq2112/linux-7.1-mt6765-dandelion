#!/usr/bin/env python3
"""ACK scan using SMBus Quick Write (same probe as i2cdetect)."""
import ctypes, fcntl, os

I2C_SMBUS = 0x0720
SMBUS_WRITE = 0
SMBUS_QUICK = 0

class SmbusData(ctypes.Structure):
    _fields_ = [("block", ctypes.c_uint8 * 34)]

class SmbusIoctl(ctypes.Structure):
    _fields_ = [("read_write", ctypes.c_uint8),
                ("command", ctypes.c_uint8),
                ("size", ctypes.c_uint32),
                ("data", SmbusData)]

def quick(bus, addr):
    try:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    except OSError:
        return False
    try:
        arg = SmbusIoctl(SMBUS_WRITE, 0, SMBUS_QUICK, SmbusData())
        fcntl.ioctl(fd, 0x0703, addr)
        fcntl.ioctl(fd, I2C_SMBUS, arg)
        return True
    except OSError:
        return False
    finally:
        os.close(fd)

for bus in range(7):
    hits = []
    for a in range(0x08, 0x78):
        if quick(bus, a):
            hits.append("%02x" % a)
    print("bus%d: %s" % (bus, " ".join(hits) if hits else "-"), flush=True)
