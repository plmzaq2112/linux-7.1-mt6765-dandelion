#!/usr/bin/env python3
"""Parse AVB vbmeta headers (big-endian) and diff device vs m3 backup."""
import struct

W = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/"
FIELDS = [
    ("magic", "4s"),
    ("req_major", "I"),
    ("req_minor", "I"),
    ("auth_block_size", "Q"),
    ("aux_block_size", "Q"),
    ("algorithm_type", "I"),
    ("hash_offset", "Q"),
    ("hash_size", "Q"),
    ("signature_offset", "Q"),
    ("signature_size", "Q"),
    ("public_key_offset", "Q"),
    ("public_key_size", "Q"),
    ("pubkey_meta_offset", "Q"),
    ("pubkey_meta_size", "Q"),
    ("descriptors_offset", "Q"),
    ("descriptors_size", "Q"),
    ("rollback_index", "Q"),
    ("flags", "I"),
    ("rollback_index_location", "I"),
    ("release_string", "48s"),
]

ALGS = {0: "NONE", 1: "SHA256_RSA2048", 2: "SHA256_RSA4096", 3: "SHA256_RSA8192",
        4: "SHA512_RSA2048", 5: "SHA512_RSA4096", 6: "SHA512_RSA8192"}


def parse(buf, label):
    print("== %s ==" % label)
    off = 0
    vals = {}
    for name, fmt in FIELDS:
        size = struct.calcsize(">" + fmt)
        v = struct.unpack(">" + fmt, buf[off:off + size])[0]
        if isinstance(v, bytes):
            v = v.rstrip(b"\x00").decode("latin1")
        vals[name] = v
        off += size
        extra = ""
        if name == "algorithm_type":
            extra = "  (%s)" % ALGS.get(v, "?")
        print("  %-24s %s%s" % (name, v, extra))
    print("  header_size = %d (reserved follows)" % off)
    print()
    return vals


now = open(W + "logs/device/recovery-pstore-2026-11-19/vbmeta-new-head.bin", "rb").read()
bak = open(W + "mt6765-mainline-m3/device-backup/vbmeta.img", "rb").read(65536)
a = parse(now, "device vbmeta (now, first 64K)")
b = parse(bak, "m3 device-backup/vbmeta.img (first 64K)")

print("differing byte offsets (first 32):")
d = [i for i in range(min(len(now), len(bak))) if now[i] != bak[i]]
print(" ", d[:32], "... total", len(d))
for off in d[:8]:
    print("   off %d: now=%02x bak=%02x" % (off, now[off], bak[off]))
print("same 4K:", now[:4096] == bak[:4096])
