#!/usr/bin/env python3
import fcntl, os, signal, sys

I2C_SLAVE = 0x0703

class Timeout(Exception):
    pass

def _alarm(signum, frame):
    raise Timeout()

signal.signal(signal.SIGALRM, _alarm)

def probe(bus, addr):
    try:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    except OSError:
        return "no-dev"
    try:
        signal.setitimer(signal.ITIMER_REAL, 1.0)
        try:
            fcntl.ioctl(fd, I2C_SLAVE, addr)
            os.read(fd, 1)
            return "ACK"
        except Timeout:
            return "TIMEOUT"
        except OSError:
            return "NAK"
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    finally:
        os.close(fd)

addrs = [0x48, 0x47, 0x44, 0x39, 0x23, 0x53, 0x1e, 0x38, 0x60, 0x49, 0x29]
for bus in range(0, 7):
    out = []
    for a in addrs:
        r = probe(bus, a)
        if r != "NAK":
            out.append("0x%02x=%s" % (a, r))
    print("i2c-%d: %s" % (bus, " ".join(out) if out else "-"), flush=True)
