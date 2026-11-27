#!/usr/bin/env python3
import fcntl, os, signal, time

I2C_SLAVE = 0x0703
class T(Exception):
    pass

def _a(s, f):
    raise T()

signal.signal(signal.SIGALRM, _a)

def probe(bus, addr, tmo=0.5):
    try:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    except OSError:
        return "nodev"
    try:
        signal.setitimer(signal.ITIMER_REAL, tmo)
        try:
            fcntl.ioctl(fd, I2C_SLAVE, addr)
            os.read(fd, 1)
            return "ACK"
        except T:
            return "TIMEOUT"
        except OSError:
            return "NAK"
        finally:
            try:
                signal.setitimer(signal.ITIMER_REAL, 0)
            except T:
                pass
    finally:
        os.close(fd)

RAILS = ["vcama", "vcamio", "vcn18", "vcn28", "vldo28", "vfe28", "vcn33-bt", "vcn33-wifi", "vefuse"]
ADDRS = [0x48, 0x47, 0x29, 0x39, 0x53, 0x1e, 0x38, 0x2c, 0x44, 0x60, 0x23, 0x10]
BUSES = [0, 1, 3]

regdir = "/sys/class/regulator"
name2path = {}
for r in os.listdir(regdir):
    p = os.path.join(regdir, r)
    try:
        name2path[open(os.path.join(p, "name")).read().strip()] = p
    except OSError:
        pass

for rail in RAILS:
    p = name2path.get(rail)
    if not p:
        print("rail %s: missing" % rail, flush=True)
        continue
    try:
        open(os.path.join(p, "state"), "w").write("enabled\n")
    except OSError as e:
        print("rail %s: cannot enable (%s)" % (rail, e), flush=True)
        continue
    time.sleep(0.2)
    hits = []
    for bus in BUSES:
        for a in ADDRS:
            r = probe(bus, a)
            if r == "ACK":
                hits.append("i2c-%d:0x%02x" % (bus, a))
    print("rail %s -> %s" % (rail, " ".join(hits) if hits else "no ACK"), flush=True)
