#!/usr/bin/env python3
"""Extract the initramfs from a boot image and print the root-selection logic."""
import struct, os, gzip, subprocess

W = "/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion"
IMG = W + "/rootfs/ubuntu/boot/images/boot-stable21-i2cclk.img"
OUT = W + "/logs/initrd21"
os.makedirs(OUT, exist_ok=True)
d = open(IMG, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
au = lambda x, p: ((x + p - 1) // p) * p
rd_off = page + au(ks, page)
rd = d[rd_off:rd_off + rs]
print("ramdisk bytes", len(rd), "magic", rd[:2].hex())
open(OUT + "/initrd.img", "wb").write(rd)
try:
    raw = gzip.decompress(rd)
    open(OUT + "/initrd.cpio", "wb").write(raw)
    print("gunzip ok", len(raw))
except Exception as e:
    print("gunzip failed:", e)
