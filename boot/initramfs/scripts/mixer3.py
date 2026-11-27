#!/usr/bin/env python3
"""ALSA mixer: list controls and set playback volumes (ctypes).

usage:
  mixer3.py vols                 list volume controls with range/current
  mixer3.py volset <name> <pct>  set playback volume to pct of range
  mixer3.py show <name>          enum items (like mixer2)
  mixer3.py enum <name> <idx>
  mixer3.py set <name> <0|1>
"""
import ctypes
import sys

lib = ctypes.CDLL("libasound.so.2")
lib.snd_strerror.restype = ctypes.c_char_p
lib.snd_mixer_open.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
lib.snd_mixer_attach.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
lib.snd_mixer_selem_register.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                         ctypes.c_void_p]
lib.snd_mixer_load.argtypes = [ctypes.c_void_p]
lib.snd_mixer_first_elem.argtypes = [ctypes.c_void_p]
lib.snd_mixer_first_elem.restype = ctypes.c_void_p
lib.snd_mixer_elem_next.argtypes = [ctypes.c_void_p]
lib.snd_mixer_elem_next.restype = ctypes.c_void_p
lib.snd_mixer_selem_get_name.argtypes = [ctypes.c_void_p]
lib.snd_mixer_selem_get_name.restype = ctypes.c_char_p
lib.snd_mixer_selem_has_playback_volume.argtypes = [ctypes.c_void_p]
lib.snd_mixer_selem_get_playback_volume_range.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long)]
lib.snd_mixer_selem_get_playback_volume.argtypes = [
    ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_long)]
lib.snd_mixer_selem_set_playback_volume_all.argtypes = [ctypes.c_void_p,
                                                        ctypes.c_long]
lib.snd_mixer_selem_get_enum_items.argtypes = [ctypes.c_void_p]
lib.snd_mixer_selem_get_enum_item_name.argtypes = [ctypes.c_void_p,
                                                   ctypes.c_uint,
                                                   ctypes.c_size_t,
                                                   ctypes.c_char_p]
lib.snd_mixer_selem_get_enum_item.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                              ctypes.POINTER(ctypes.c_uint)]
lib.snd_mixer_selem_set_enum_item.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                              ctypes.c_uint]
lib.snd_mixer_selem_set_playback_switch_all.argtypes = [ctypes.c_void_p,
                                                        ctypes.c_int]
lib.snd_mixer_selem_set_capture_switch_all.argtypes = [ctypes.c_void_p,
                                                       ctypes.c_int]

SND_MIXER_SCHN_FRONT_LEFT = 0

m = ctypes.c_void_p()
lib.snd_mixer_open(ctypes.byref(m), 0)
lib.snd_mixer_attach(m, b"hw:0")
lib.snd_mixer_selem_register(m, None, None)
lib.snd_mixer_load(m)


def find(name):
    e = lib.snd_mixer_first_elem(m)
    while e:
        if lib.snd_mixer_selem_get_name(e) == name.encode():
            return e
        e = lib.snd_mixer_elem_next(e)
    return None


cmd = sys.argv[1]
if cmd == "vols":
    e = lib.snd_mixer_first_elem(m)
    while e:
        if lib.snd_mixer_selem_has_playback_volume(e):
            lo, hi = ctypes.c_long(), ctypes.c_long()
            lib.snd_mixer_selem_get_playback_volume_range(e, ctypes.byref(lo),
                                                          ctypes.byref(hi))
            cur = ctypes.c_long()
            lib.snd_mixer_selem_get_playback_volume(
                e, SND_MIXER_SCHN_FRONT_LEFT, ctypes.byref(cur))
            print("%-32s %ld..%ld cur=%ld" % (
                lib.snd_mixer_selem_get_name(e).decode(), lo.value, hi.value,
                cur.value))
        e = lib.snd_mixer_elem_next(e)
elif cmd == "volset":
    e = find(sys.argv[2])
    if not e:
        print("not found"); sys.exit(1)
    pct = int(sys.argv[3])
    lo, hi = ctypes.c_long(), ctypes.c_long()
    lib.snd_mixer_selem_get_playback_volume_range(e, ctypes.byref(lo),
                                                  ctypes.byref(hi))
    val = lo.value + (hi.value - lo.value) * pct // 100
    lib.snd_mixer_selem_set_playback_volume_all(e, val)
    print("set %s = %d (%d%%)" % (sys.argv[2], val, pct))
elif cmd == "show":
    e = find(sys.argv[2])
    if not e:
        print("not found"); sys.exit(1)
    n = lib.snd_mixer_selem_get_enum_items(e)
    print("enum items:", n)
    for i in range(n):
        buf = ctypes.create_string_buffer(128)
        lib.snd_mixer_selem_get_enum_item_name(e, i, 128, buf)
        cur = ctypes.c_uint(99)
        lib.snd_mixer_selem_get_enum_item(e, 0, ctypes.byref(cur))
        print("  %d: %s%s" % (i, buf.value.decode(),
                              "  <= current" if cur.value == i else ""))
elif cmd == "enum":
    e = find(sys.argv[2])
    if not e:
        print("not found"); sys.exit(1)
    lib.snd_mixer_selem_set_enum_item(e, 0, int(sys.argv[3]))
    print("ok")
elif cmd == "set":
    e = find(sys.argv[2])
    if not e:
        print("not found"); sys.exit(1)
    v = int(sys.argv[3])
    lib.snd_mixer_selem_set_playback_switch_all(e, v)
    lib.snd_mixer_selem_set_capture_switch_all(e, v)
    print("ok")
