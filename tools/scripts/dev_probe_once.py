#!/usr/bin/env python3
"""Probe a short list of sensor addresses on all AP i2c buses."""
import fcntl, os, signal

I2C_SLAVE = 0x0703
class T(Exception):
    pass

def _a(s, f):
    raise T()

signal.signal(signal.SIGALRM, _a)

def probe(bus, addr, tmo=0.4):
    try:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    except OSError:
        return None
    try:
        signal.setitimer(signal.ITIMER_REAL, tmo)
        try:
            fcntl.ioctl(fd, I2C_SLAVE, addr)
            os.read(fd, 1)
            return "ACK"
        except T:
            return None
        except OSError:
            return None
        finally:
            try:
                signal.setitimer(signal.ITIMER_REAL, 0)
            except T:
                pass
    finally:
        os.close(fd)

ADDRS = [0x48, 0x47, 0x29, 0x39, 0x53, 0x1e, 0x38, 0x2c, 0x44, 0x60, 0x23,
         0x18, 0x19, 0x68, 0x69, 0x4c, 0x6a, 0x6b, 0x0e, 0x0f, 0x10, 0x11]

hits = []
for bus in range(0, 7):
    for a in ADDRS:
        if probe(bus, a) == "ACK":
            hits.append("i2c-%d:0x%02x" % (bus, a))
print("  ACK: " + (" ".join(hits) if hits else "none"), flush=True)
