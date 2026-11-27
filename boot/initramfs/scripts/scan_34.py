#!/usr/bin/env python3
"""Probe address 0x34 on every /dev/i2c-N."""
import errno
import fcntl
import os

I2C_SLAVE = 0x0703
ADDR = 0x34

for bus in range(0, 10):
    path = "/dev/i2c-%d" % bus
    if not os.path.exists(path):
        continue
    try:
        fd = os.open(path, os.O_RDWR)
    except OSError as e:
        print("i2c-%d: open failed %d" % (bus, e.errno))
        continue
    try:
        fcntl.ioctl(fd, I2C_SLAVE, ADDR)
        try:
            data = os.read(fd, 1)
            print("i2c-%d 0x%02x ACK read=%r" % (bus, ADDR, data))
        except OSError as e:
            if e.errno in (errno.EREMOTEIO, errno.ENXIO):
                print("i2c-%d 0x%02x no ack" % (bus, ADDR))
            else:
                print("i2c-%d 0x%02x err %d" % (bus, ADDR, e.errno))
    finally:
        os.close(fd)
