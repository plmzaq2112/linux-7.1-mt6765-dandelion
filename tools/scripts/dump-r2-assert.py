#!/usr/bin/env python3
"""Dump LK log context around the newest r2 boot attempts."""
p = ("/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/"
     "logs/device/recovery-pstore-2026-11-19/expdb2.bin")
d = open(p, "rb").read()

for off in (20131713, 20342176, 20551036):
    print("=" * 30, "context before/after", off)
    print(d[max(0, off - 3500):off + 700].decode("latin1"))
    print()
