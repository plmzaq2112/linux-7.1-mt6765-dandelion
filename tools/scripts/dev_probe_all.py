#!/usr/bin/env python3
"""Probe sensor addresses on all buses."""
import fcntl, os

I2C_SLAVE = 0x0703
ADDRS = [0x18, 0x19, 0x48, 0x47, 0x29, 0x39, 0x53, 0x1e, 0x38, 0x2c]

def probe(bus, addr):
    try:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    except OSError:
        return None
    try:
        fcntl.ioctl(fd, I2C_SLAVE, addr)
        os.read(fd, 1)
        return True
    except OSError:
        return False
    finally:
        os.close(fd)

for bus in range(7):
    found = []
    for a in ADDRS:
        if probe(bus, a):
            found.append("0x%02x" % a)
    print("  bus%d: %s" % (bus, " ".join(found) if found else "-"), flush=True)
