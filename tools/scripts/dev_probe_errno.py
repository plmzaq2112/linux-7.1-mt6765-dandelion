#!/usr/bin/env python3
"""Probe one bus/addr and print the raw errno: 0=ACK, 6=NAK, 110=timeout."""
import fcntl, os, sys

I2C_SLAVE = 0x0703
bus, addr = int(sys.argv[1]), int(sys.argv[2], 0)
try:
    fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
except OSError as e:
    print("open:%s" % e.errno); sys.exit(0)
try:
    fcntl.ioctl(fd, I2C_SLAVE, addr)
    os.write(fd, bytes([0x0f, 0x00]))
    print("0")
except OSError as e:
    print("%d" % e.errno)
finally:
    os.close(fd)
