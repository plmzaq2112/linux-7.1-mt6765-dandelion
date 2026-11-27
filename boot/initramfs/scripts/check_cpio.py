import gzip, struct, sys

p = "/tmp/db/ramdisk-new.gz"
data = gzip.decompress(open(p, "rb").read())
off = 0
found = 0
while off + 110 <= len(data):
    if data[off:off+6] not in (b"070701", b"070702"):
        print("bad magic at", off, data[off:off+6]); break
    hdr = data[off:off+110]
    f = lambda i: int(hdr[6+8*i:14+8*i], 16)
    ino, mode, uid, gid, nlink, mtime, size = f(0), f(1), f(2), f(3), f(4), f(5), f(6)
    namesize = f(11)
    name = data[off+110:off+110+namesize-1].decode()
    if name in ("./init", "init"):
        print("FOUND", name, "mode=%o uid=%d gid=%d size=%d" % (mode, uid, gid, size))
        found += 1
    off += 110 + namesize
    off = (off + 3) & ~3
    off += size
    off = (off + 3) & ~3
    if name == "TRAILER!!!":
        break
print("entries scanned, found:", found, "total bytes:", len(data))
