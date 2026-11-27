#!/usr/bin/env python3
"""List (and optionally set) ALSA mixer controls with ctypes.

usage: mixer.py list [card]
       mixer.py set <name> <value>
"""
import ctypes
import sys

lib = ctypes.CDLL("libasound.so.2")
lib.snd_strerror.restype = ctypes.c_char_p
lib.snd_strerror.argtypes = [ctypes.c_int]
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
lib.snd_mixer_selem_has_playback_switch.argtypes = [ctypes.c_void_p]
lib.snd_mixer_selem_set_playback_switch_all.argtypes = [ctypes.c_void_p,
                                                        ctypes.c_int]
lib.snd_mixer_selem_set_capture_switch_all.argtypes = [ctypes.c_void_p,
                                                       ctypes.c_int]
lib.snd_mixer_selem_has_capture_switch.argtypes = [ctypes.c_void_p]


def open_mixer(card):
    m = ctypes.c_void_p()
    rc = lib.snd_mixer_open(ctypes.byref(m), 0)
    assert rc == 0, lib.snd_strerror(rc)
    rc = lib.snd_mixer_attach(m, ("hw:%s" % card).encode())
    assert rc == 0, lib.snd_strerror(rc)
    rc = lib.snd_mixer_selem_register(m, None, None)
    assert rc == 0, lib.snd_strerror(rc)
    rc = lib.snd_mixer_load(m)
    assert rc == 0, lib.snd_strerror(rc)
    return m


cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
m = open_mixer(sys.argv[2] if cmd == "list" and len(sys.argv) > 2 else "0")

if cmd == "list":
    elem = lib.snd_mixer_first_elem(m)
    while elem:
        name = lib.snd_mixer_selem_get_name(elem).decode()
        kind = []
        if lib.snd_mixer_selem_has_playback_switch(elem):
            kind.append("P")
        if lib.snd_mixer_selem_has_capture_switch(elem):
            kind.append("C")
        print("%s %s" % ("/".join(kind) or "-", name))
        elem = lib.snd_mixer_elem_next(elem)
elif cmd == "set":
    name = sys.argv[2].encode()
    val = int(sys.argv[3])
    elem = lib.snd_mixer_first_elem(m)
    found = False
    while elem:
        if lib.snd_mixer_selem_get_name(elem) == name:
            found = True
            if lib.snd_mixer_selem_has_playback_switch(elem):
                print("set playback", name.decode(), val)
                lib.snd_mixer_selem_set_playback_switch_all(elem, val)
            if lib.snd_mixer_selem_has_capture_switch(elem):
                print("set capture", name.decode(), val)
                lib.snd_mixer_selem_set_capture_switch_all(elem, val)
            break
        elem = lib.snd_mixer_elem_next(elem)
    if not found:
        print("not found:", name.decode())
