#!/usr/bin/env python3
"""Print the GPT partition names from /dev/mmcblk0 (read-only)."""
import struct

fd = open("/dev/mmcblk0", "rb")

# GPT header at LBA1 (512-byte sectors)
fd.seek(512)
hdr = fd.read(92)
assert hdr[:8] == b"EFI PART", "no GPT"
entries_lba = struct.unpack_from("<Q", hdr, 72)[0]
num_entries = struct.unpack_from("<I", hdr, 80)[0]
entry_size = struct.unpack_from("<I", hdr, 84)[0]

fd.seek(entries_lba * 512)
data = fd.read(num_entries * entry_size)
for i in range(num_entries):
    e = data[i * entry_size:(i + 1) * entry_size]
    if e[:16] == b"\x00" * 16:
        continue
    first = struct.unpack_from("<Q", e, 32)[0]
    last = struct.unpack_from("<Q", e, 40)[0]
    name = e[56:128].decode("utf-16le", "replace").rstrip("\x00")
    print("p%-3d %-24s %8d..%8d  %d MiB" %
          (i + 1, name, first, last, (last - first + 1) // 2048))
fd.close()
