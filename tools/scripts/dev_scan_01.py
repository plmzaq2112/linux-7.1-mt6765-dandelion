#!/usr/bin/env python3
"""Scan i2c-gpio buses 7/8 (i2c0/i2c1) at 50 kHz."""
import fcntl, os

I2C_SLAVE = 0x0703

def quick(bus, addr):
    try:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    except OSError:
        return None
    try:
        fcntl.ioctl(fd, I2C_SLAVE, addr)
        os.write(fd, bytes([0x0f, 0x00]))
        return True
    except OSError:
        return False
    finally:
        os.close(fd)

for bus in (7, 8):
    hits = []
    for a in range(0x08, 0x78):
        if quick(bus, a):
            hits.append("0x%02x" % a)
    print("i2c-%d: %s" % (bus, " ".join(hits) if hits else "-"), flush=True)
