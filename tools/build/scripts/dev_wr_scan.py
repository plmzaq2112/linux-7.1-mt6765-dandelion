#!/usr/bin/env python3
"""Presence probe: write reg 0x0f = 0x00 (ACK means chip present)."""
import fcntl, os

I2C_SLAVE = 0x0703
RANGES = list(range(0x18, 0x20)) + list(range(0x28, 0x30)) + \
         list(range(0x38, 0x40)) + list(range(0x44, 0x50))

def probe(bus, addr):
    try:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    except OSError:
        return None
    try:
        fcntl.ioctl(fd, I2C_SLAVE, addr)
        os.write(fd, bytes([0x0f, 0x00]))
        return "ACK"
    except OSError as e:
        return "BUSY" if e.errno == 16 else None
    finally:
        os.close(fd)

for bus in range(7):
    hits = []
    for a in RANGES:
        r = probe(bus, a)
        if r:
            hits.append("%02x=%s" % (a, r))
    print("bus%d: %s" % (bus, " ".join(hits) if hits else "-"), flush=True)
