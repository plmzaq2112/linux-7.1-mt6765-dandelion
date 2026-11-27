#!/usr/bin/env python3
"""Dump the first registers of the device found at 0x47 on the bit-banged bus."""
import fcntl, os, sys

I2C_SLAVE = 0x0703
bus = int(sys.argv[1])
addr = int(sys.argv[2], 0)

fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
fcntl.ioctl(fd, I2C_SLAVE, addr)
out = []
for reg in range(0x00, 0x20):
    try:
        os.write(fd, bytes([reg]))
        v = os.read(fd, 1)
        out.append("%02x:%s" % (reg, v.hex()))
    except OSError as e:
        out.append("%02x:E%d" % (reg, e.errno))
print(" ".join(out))
os.close(fd)
