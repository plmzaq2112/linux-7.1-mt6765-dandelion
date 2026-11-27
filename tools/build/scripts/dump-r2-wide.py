#!/usr/bin/env python3
"""Dump a wider window before the r2 'g_boot_info.hdr_loaded' assert."""
p = ("/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/"
     "logs/device/recovery-pstore-2026-11-19/expdb2.bin")
d = open(p, "rb").read()
start, end = 20060000, 20131800
txt = d[start:end].decode("latin1")
# keep only lines that look like LK log lines / boot text
print(txt)
