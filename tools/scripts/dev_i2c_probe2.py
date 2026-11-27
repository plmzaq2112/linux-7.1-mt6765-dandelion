#!/usr/bin/env python3
import fcntl, os, signal, time

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
    res = "NAK"
    try:
        signal.setitimer(signal.ITIMER_REAL, 2.0)
        try:
            fcntl.ioctl(fd, I2C_SLAVE, addr)
            os.read(fd, 1)
            res = "ACK"
        except Timeout:
            res = "TIMEOUT"
        except OSError:
            res = "NAK"
        finally:
            try:
                signal.setitimer(signal.ITIMER_REAL, 0)
            except Timeout:
                pass
    finally:
        os.close(fd)
    return res

addrs = [0x48, 0x47, 0x44, 0x39, 0x23, 0x53, 0x1e, 0x38, 0x60, 0x49, 0x29, 0x2c]
for bus in range(0, 7):
    t0 = time.time()
    out = []
    for a in addrs:
        r = probe(bus, a)
        if r != "NAK":
            out.append("0x%02x=%s" % (a, r))
    print("i2c-%d (%.1fs): %s" % (bus, time.time() - t0,
                                  " ".join(out) if out else "-"), flush=True)
