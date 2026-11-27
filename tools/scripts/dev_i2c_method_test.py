#!/usr/bin/env python3
import fcntl, os

I2C_SLAVE = 0x0703

def t(bus, addr, label, fn):
    try:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    except OSError as e:
        print("%s: open %s" % (label, e)); return
    try:
        fcntl.ioctl(fd, I2C_SLAVE, addr)
        print("%s: %s" % (label, fn(fd)))
    except OSError as e:
        print("%s: ERR %s (%s)" % (label, e.errno, e.strerror))
    finally:
        os.close(fd)

addr = 0x6b
t(5, addr, "write 1 byte", lambda fd: os.write(fd, bytes([0x00])))
t(5, addr, "write 2 bytes", lambda fd: os.write(fd, bytes([0x00, 0x00])))
t(5, addr, "read 1 byte", lambda fd: os.read(fd, 1).hex())

def rd(fd):
    os.write(fd, bytes([0x00]))
    return os.read(fd, 2).hex()
t(5, addr, "reg read 0x00", rd)

def rd2(fd):
    os.write(fd, bytes([0x09]))
    return os.read(fd, 2).hex()
t(5, addr, "reg read 0x09", rd2)
