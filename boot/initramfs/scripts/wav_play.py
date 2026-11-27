#!/usr/bin/env python3
"""Play a WAV file through ALSA hw:0,0 (ctypes, no alsa-utils).

usage: wav_play.py <file.wav> [device]
"""
import ctypes
import sys
import wave

lib = ctypes.CDLL("libasound.so.2")
SND_PCM_STREAM_PLAYBACK = 0
SND_PCM_FORMAT_S16_LE = 2
SND_PCM_ACCESS_RW_INTERLEAVED = 3

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

path = sys.argv[1]
dev = (sys.argv[2] if len(sys.argv) > 2 else "hw:0,0").encode()

w = wave.open(path, "rb")
ch = w.getnchannels()
sw = w.getsampwidth()
rate = w.getframerate()
print("wav: %d ch, %d bytes/sample, %d Hz, %d frames" %
      (ch, sw, rate, w.getnframes()))
if sw != 2 or ch != 2:
    print("only 16-bit stereo supported")
    sys.exit(1)

pcm = ctypes.c_void_p()
rc = lib.snd_pcm_open(ctypes.byref(pcm), dev, SND_PCM_STREAM_PLAYBACK, 0)
print("open ->", rc, lib.snd_strerror(rc).decode())
if rc < 0:
    sys.exit(1)
rc = lib.snd_pcm_set_params(pcm, SND_PCM_FORMAT_S16_LE,
                            SND_PCM_ACCESS_RW_INTERLEAVED,
                            ch, rate, 1, 200000)
print("params ->", rc, lib.snd_strerror(rc).decode())
if rc < 0:
    sys.exit(1)

CHUNK = 4096
total = 0
while True:
    data = w.readframes(CHUNK)
    if not data:
        break
    frames = len(data) // (2 * ch)
    cbuf = (ctypes.c_char * len(data)).from_buffer_copy(data)
    off = 0
    while off < frames:
        ptr = ctypes.cast(ctypes.byref(cbuf, off * 2 * ch), ctypes.c_void_p)
        rc = lib.snd_pcm_writei(pcm, ptr, frames - off)
        if rc < 0:
            rc = lib.snd_pcm_recover(pcm, rc, 1)
            if rc < 0:
                print("recover failed", lib.snd_strerror(rc).decode())
                break
            continue
        off += rc
    total += off
w.close()
lib.snd_pcm_drain(pcm)
lib.snd_pcm_close(pcm)
print("played %d frames" % total)
