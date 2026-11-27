#!/usr/bin/env python3
import fcntl, os, sys

I2C_SLAVE = 0x0703

def probe(bus, addr):
    path = "/dev/i2c-%d" % bus
    try:
        fd = os.open(path, os.O_RDWR)
    except OSError as e:
        return None
    try:
        fcntl.ioctl(fd, I2C_SLAVE, addr)
        os.read(fd, 1)
        return True
    except OSError:
        return False
    finally:
        os.close(fd)

for bus in range(0, 7):
    found = []
    for addr in range(0x08, 0x78):
        if probe(bus, addr):
            found.append("0x%02x" % addr)
    print("i2c-%d: %s" % (bus, " ".join(found) if found else "-"))
