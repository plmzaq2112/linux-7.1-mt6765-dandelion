#!/usr/bin/env python3
"""Play a sine tone through ALSA (ctypes), looping writei.

usage: alsa_test.py [device] [seconds] [freq]
"""
import ctypes
import math
import struct
import sys

lib = ctypes.CDLL("libasound.so.2")
SND_PCM_STREAM_PLAYBACK = 0
SND_PCM_FORMAT_S16_LE = 2
SND_PCM_ACCESS_RW_INTERLEAVED = 3
SND_PCM_ACCESS = ctypes.c_void_p

lib.snd_strerror.restype = ctypes.c_char_p
lib.snd_strerror.argtypes = [ctypes.c_int]
lib.snd_pcm_open.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p,
                             ctypes.c_int, ctypes.c_int]
lib.snd_pcm_set_params.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_uint, ctypes.c_uint, ctypes.c_int,
                                   ctypes.c_uint]
lib.snd_pcm_writei.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
lib.snd_pcm_writei.restype = ctypes.c_long
lib.snd_pcm_drain.argtypes = [ctypes.c_void_p]
lib.snd_pcm_close.argtypes = [ctypes.c_void_p]
lib.snd_pcm_recover.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

dev = (sys.argv[1] if len(sys.argv) > 1 else "hw:0,0").encode()
secs = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
freq = float(sys.argv[3]) if len(sys.argv) > 3 else 440.0
rate = int(sys.argv[4]) if len(sys.argv) > 4 else 44100

pcm = ctypes.c_void_p()
rc = lib.snd_pcm_open(ctypes.byref(pcm), dev, SND_PCM_STREAM_PLAYBACK, 0)
print("open ->", rc, lib.snd_strerror(rc).decode())
if rc < 0:
    sys.exit(1)
rc = lib.snd_pcm_set_params(pcm, SND_PCM_FORMAT_S16_LE,
                            SND_PCM_ACCESS_RW_INTERLEAVED,
                            2, rate, 1, 500000)
print("params ->", rc, lib.snd_strerror(rc).decode())
if rc < 0:
    sys.exit(1)

frames = int(rate * secs)
buf = bytearray()
fade = int(rate * 0.05)
total = frames
for i in range(frames):
    env = 1.0
    if i < fade:
        env = i / fade
    elif i > total - fade:
        env = (total - i) / fade
    v = int(20000 * env * math.sin(2 * math.pi * freq * i / rate))
    buf += struct.pack("<hh", v, v)

cbuf = (ctypes.c_char * len(buf)).from_buffer(buf)
off = 0
while off < frames:
    ptr = ctypes.cast(ctypes.byref(cbuf, off * 4), ctypes.c_void_p)
    rc = lib.snd_pcm_writei(pcm, ptr, frames - off)
    if rc < 0:
        rc = lib.snd_pcm_recover(pcm, rc, 1)
        if rc < 0:
            print("recover failed", lib.snd_strerror(rc).decode())
            break
        continue
    off += rc
print("written %d/%d frames" % (off, frames))
lib.snd_pcm_drain(pcm)
lib.snd_pcm_close(pcm)
print("done")
