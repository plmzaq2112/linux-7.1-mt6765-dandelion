#!/usr/bin/env python3
"""Scan I2C buses for the AW87519 (and anything else that ACKs)."""
import errno
import fcntl
import os

I2C_SLAVE = 0x0703


def probe(bus, addr):
    path = "/dev/i2c-%d" % bus
    try:
        fd = os.open(path, os.O_RDWR)
    except OSError:
        return None
    try:
        fcntl.ioctl(fd, I2C_SLAVE, addr)
        try:
            os.read(fd, 1)
            return "ack"
        except OSError as e:
            if e.errno in (errno.EREMOTEIO, errno.ENXIO):
                return None
            return "err%d" % e.errno
    finally:
        os.close(fd)


for bus in range(0, 8):
    path = "/dev/i2c-%d" % bus
    if not os.path.exists(path):
        continue
    found = []
    for addr in range(0x03, 0x78):
        r = probe(bus, addr)
        if r:
            found.append("0x%02x(%s)" % (addr, r))
    print("i2c-%d: %s" % (bus, " ".join(found) if found else "(none)"))
