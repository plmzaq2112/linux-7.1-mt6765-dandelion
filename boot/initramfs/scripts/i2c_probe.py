#!/usr/bin/env python3
"""Probe one I2C address (default i2c-3 0x34)."""
import errno
import fcntl
import os
import sys

bus = int(sys.argv[1]) if len(sys.argv) > 1 else 3
addr = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x34
I2C_SLAVE = 0x0703

fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
try:
    fcntl.ioctl(fd, I2C_SLAVE, addr)
    data = os.read(fd, 1)
    print("i2c-%d 0x%02x ACK, read=%r" % (bus, addr, data))
except OSError as e:
    if e.errno in (errno.EREMOTEIO, errno.ENXIO):
        print("i2c-%d 0x%02x NO ACK (errno %d)" % (bus, addr, e.errno))
    else:
        print("i2c-%d 0x%02x error %d" % (bus, addr, e.errno))
finally:
    os.close(fd)
