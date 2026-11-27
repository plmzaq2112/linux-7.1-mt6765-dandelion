import struct, subprocess, os, sys

p = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/logs/device/recovery-pstore-2026-11-19/dtbo.bin"
d = open(p, "rb").read()

magic, total, hdr_size, entry_size, entry_count, entry_size2 = struct.unpack_from(">6I", d, 0)
print("magic=%08x total=%d hdr=%d entry=%d count=%d" % (magic, total, hdr_size, entry_size, entry_count, entry_size2))

found = []
for i in range(entry_count):
    off = hdr_size + i * entry_size
    sz, dtoff, dtisz = struct.unpack_from(">III", d, off)
    blob = d[dtoff:dtoff + sz]
    if blob[:4] != b"\xd0\x0d\xfe\xed":
        continue
    if b"lcd-backlight" in blob or b"mt6370" in blob:
        found.append((i, dtoff, sz))

print("candidate fragments:", [(i, s) for i, o, s in found])

for i, off, sz in found:
    blob = d[off:off + sz]
    fn = "/home/a12bbb/frag%d.dtb" % i
    open(fn, "wb").write(blob)
    out = "/home/a12bbb/frag%d.dts" % i
    subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", out, fn],
                   capture_output=True)
    print("wrote", out)
