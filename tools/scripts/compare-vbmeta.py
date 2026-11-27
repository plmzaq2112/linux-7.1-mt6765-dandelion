#!/usr/bin/env python3
"""Compare on-device vbmeta (8 MiB) with the m3 device-backup vbmeta.img."""
W = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/"
now = open(W + "logs/device/recovery-pstore-2026-11-19/vbmeta-full.bin", "rb").read()
bak = open(W + "mt6765-mainline-m3/device-backup/vbmeta.img", "rb").read()
print("sizes: now=%d backup=%d" % (len(now), len(bak)))
n = min(len(now), len(bak))

# non-zero blocks of 4K in the live partition
blocks = [i for i in range(0, n, 4096) if any(now[i:i + 4096])]
print("live: non-zero 4K blocks: %d, first=%s last=%s"
      % (len(blocks), blocks[0] if blocks else None, blocks[-1] if blocks else None))

diffs = [i for i in range(n) if now[i] != bak[i]]
print("differing bytes: %d" % len(diffs))
if diffs:
    print("  first diff off=%d (0x%x), last diff off=%d (0x%x)"
          % (diffs[0], diffs[0], diffs[-1], diffs[-1]))
    # contiguous diff ranges
    ranges = []
    s = prev = diffs[0]
    for i in diffs[1:]:
        if i != prev + 1:
            ranges.append((s, prev))
            s = i
        prev = i
    ranges.append((s, prev))
    print("  diff ranges (up to 10):")
    for s, e in ranges[:10]:
        print("    0x%x - 0x%x  (%d bytes)" % (s, e, e - s + 1))

# where does meaningful content start in the live partition?
start = next((i for i, b in enumerate(now) if b), None)
print("live first non-zero byte at:", start)
print("live AVB0 count:", now.count(b"AVB0"), "backup AVB0 count:", bak.count(b"AVB0"))
