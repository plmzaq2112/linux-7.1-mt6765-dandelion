#!/usr/bin/env python3
"""Ambient-light auto brightness for Redmi 9A (dandelion) — v3 behaviour.

First version that felt right: piecewise lux curve, 20 % hysteresis, smooth
1 %-per-tick ramp over gsd-power's session D-Bus.
"""
import ctypes, fcntl, math, os, sys, time

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

I2C_RDWR = 0x0707
BUS = int(os.environ.get("ALS_BUS", "8"))
ADDR = int(os.environ.get("ALS_ADDR", "0x47"), 0)

CURVE = [(0, 10), (16, 12), (32, 20), (48, 32), (64, 45),
         (96, 58), (128, 72), (170, 88), (210, 100)]
HYST_LOG = math.log(1.20)
ALPHA = 0.25
RAMP = 1          # percent per tick
TICK = 0.05       # 20 Hz
READ_EVERY = 0.3  # ALS sample period

class Msg(ctypes.Structure):
    _fields_ = [("addr", ctypes.c_uint16), ("flags", ctypes.c_uint16),
                ("len", ctypes.c_uint16), ("buf", ctypes.POINTER(ctypes.c_uint8))]

class Rdwr(ctypes.Structure):
    _fields_ = [("msgs", ctypes.POINTER(Msg)), ("nmsgs", ctypes.c_uint32)]

def xfer(fd, w, rlen):
    wb = (ctypes.c_uint8 * max(1, len(w)))(*w)
    rb = (ctypes.c_uint8 * max(1, rlen))()
    msgs = [Msg(ADDR, 0, len(w), ctypes.cast(wb, ctypes.POINTER(ctypes.c_uint8)))]
    if rlen:
        msgs.append(Msg(ADDR, 1, rlen, ctypes.cast(rb, ctypes.POINTER(ctypes.c_uint8))))
    arr = (Msg * len(msgs))(*msgs)
    d = Rdwr(ctypes.cast(arr, ctypes.POINTER(Msg)), len(msgs))
    fcntl.ioctl(fd, I2C_RDWR, d)
    return list(rb)

def curve(c):
    if c <= CURVE[0][0]:
        return CURVE[0][1]
    for (c0, p0), (c1, p1) in zip(CURVE, CURVE[1:]):
        if c <= c1:
            return p0 + (p1 - p0) * (c - c0) / (c1 - c0)
    return CURVE[-1][1]

def main():
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

    def set_pct(pct):
        bus.call_sync(
            "org.gnome.SettingsDaemon.Power",
            "/org/gnome/SettingsDaemon/Power",
            "org.freedesktop.DBus.Properties", "Set",
            GLib.Variant("(ssv)", ("org.gnome.SettingsDaemon.Power.Screen",
                                   "Brightness", GLib.Variant("i", int(pct)))),
            None, Gio.DBusCallFlags.NONE, 2000, None)

    fd = os.open("/dev/i2c-%d" % BUS, os.O_RDWR)
    try:
        xfer(fd, [0x00, 0x00], 0)
        xfer(fd, [0x02, 0x23], 0)
        xfer(fd, [0x00, 0x02], 0)
    except OSError as e:
        print("ALS init failed:", e, flush=True)
        return 1
    time.sleep(0.5)

    ema = None
    anchor = None
    target = None
    cur = None
    applied = None
    t_read = 0.0

    while True:
        now = time.time()
        if now - t_read >= READ_EVERY:
            t_read = now
            try:
                b = xfer(fd, [0x00], 0x1F)
                counts = float(b[0x14])
                ema = counts if ema is None else ema * (1 - ALPHA) + counts * ALPHA
            except OSError as e:
                print("read error:", e, flush=True)
                time.sleep(1)
                continue

            if anchor is None or abs(math.log(ema + 1) - math.log(anchor + 1)) > HYST_LOG:
                target = curve(ema)
                anchor = ema
                print("als=%d ema=%.1f target=%d%%" % (counts, ema, target), flush=True)

        if target is not None:
            if cur is None:
                cur = target
            elif cur != target:
                cur += RAMP if target > cur else -RAMP
            if applied is None or int(cur) != applied:
                try:
                    set_pct(int(cur))
                    applied = int(cur)
                except Exception as e:
                    print("dbus error:", e, flush=True)

        time.sleep(TICK)

if __name__ == "__main__":
    sys.exit(main())
