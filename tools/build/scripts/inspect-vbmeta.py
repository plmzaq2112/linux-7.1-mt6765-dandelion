#!/usr/bin/env python3
"""Inspect the on-device vbmeta partition head vs the m3 backup."""
import hashlib

W = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/"
now = open(W + "logs/device/recovery-pstore-2026-11-19/vbmeta-now-head.bin", "rb").read()
bak = open(W + "mt6765-mainline-m3/device-backup/vbmeta.img", "rb").read(65536)

first = next((i for i, b in enumerate(now) if b), None)
print("now: len=%d first_nonzero_off=%s md5=%s" % (len(now), first, hashlib.md5(now).hexdigest()))
print("backup head: md5=%s starts=%r" % (hashlib.md5(bak).hexdigest(), bak[:8]))
print("backup AVB0 count in 64K:", bak.count(b"AVB0"), "| now AVB0 count:", now.count(b"AVB0"),
      "| now ANDROID! count:", now.count(b"ANDROID!"))

for name, buf in (("now", now), ("backup", bak)):
    print("\n%s first 96 bytes:" % name)
    for off in range(0, 96, 16):
        chunk = buf[off:off + 16]
        print("  %04x  %s  %s" % (off, " ".join("%02x" % c for c in chunk),
                                  "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)))

if first is not None:
    print("\nnow around first_nonzero:")
    lo = max(0, first - 16)
    print("  ", now[lo:lo + 96].hex())

diff = sum(1 for a, b in zip(now, bak) if a != b)
print("\nbyte diffs in first 64K: %d / %d" % (diff, len(now)))
