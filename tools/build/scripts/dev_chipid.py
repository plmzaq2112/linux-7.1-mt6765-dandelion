#!/usr/bin/env python3
"""Read sensor chip-id registers over i2c-dev (write reg, read n bytes)."""
import fcntl, os, sys

I2C_SLAVE = 0x0703

def read_reg(bus, addr, reg, n=1):
    fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    try:
        fcntl.ioctl(fd, I2C_SLAVE, addr)
        os.write(fd, bytes([reg]))
        return os.read(fd, n).hex()
    except OSError as e:
        return "ERR(%s)" % e.errno
    finally:
        os.close(fd)

def main():
    bus = int(sys.argv[1])
    addrs = [int(a, 0) for a in sys.argv[2:]] or [0x18, 0x19, 0x48, 0x47, 0x29, 0x39]
    for a in addrs:
        line = ["i2c-%d 0x%02x:" % (bus, a)]
        # generic: reg 0x00, 0x01, 0x0f, 0x0d
        for reg in (0x00, 0x01, 0x0d, 0x0f):
            line.append("r%02x=%s" % (reg, read_reg(bus, a, reg)))
        print(" ".join(line), flush=True)

main()
