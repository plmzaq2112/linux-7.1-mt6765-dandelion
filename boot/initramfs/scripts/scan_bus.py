#!/usr/bin/env python3
"""Full scan of one i2c bus (default i2c-3, bit-banged)."""
import errno
import fcntl
import os
import sys

I2C_SLAVE = 0x0703
bus = int(sys.argv[1]) if len(sys.argv) > 1 else 3

fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
found = []
for addr in range(0x03, 0x78):
    try:
        fcntl.ioctl(fd, I2C_SLAVE, addr)
        try:
            os.read(fd, 1)
            found.append("0x%02x" % addr)
        except OSError as e:
            if e.errno not in (errno.EREMOTEIO, errno.ENXIO):
                found.append("0x%02x(err%d)" % (addr, e.errno))
    except OSError:
        pass
os.close(fd)
print("i2c-%d: %s" % (bus, " ".join(found) if found else "(no devices)"))
