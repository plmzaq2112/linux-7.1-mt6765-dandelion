#!/usr/bin/env python3
"""Scan the i2c-gpio buses created on the SCP sensor pins."""
import fcntl, os

I2C_SLAVE = 0x0703
BUSES = [7, 8, 9, 10]

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

for bus in BUSES:
    hits = []
    for a in range(0x08, 0x78):
        if quick(bus, a):
            hits.append("0x%02x" % a)
    print("i2c-%d: %s" % (bus, " ".join(hits) if hits else "-"), flush=True)
