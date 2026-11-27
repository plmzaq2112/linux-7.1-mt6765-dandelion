#!/usr/bin/env python3
import fcntl, os

I2C_SLAVE = 0x0703

for bus, addr in [(5, 0x1a), (5, 0x34), (5, 0x6b), (2, 0x20), (3, 0x34), (1, 0x48)]:
    try:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    except OSError as e:
        print("bus%d 0x%02x open=%s" % (bus, addr, e)); continue
    try:
        try:
            fcntl.ioctl(fd, I2C_SLAVE, addr)
        except OSError as e:
            print("bus%d 0x%02x slave=%s" % (bus, addr, e.errno)); continue
        try:
            n = os.write(fd, bytes([0x0f, 0x00]))
            print("bus%d 0x%02x write=ok(%d)" % (bus, addr, n))
        except OSError as e:
            print("bus%d 0x%02x write=%s" % (bus, addr, e.errno))
    finally:
        os.close(fd)
