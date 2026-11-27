import struct, os, hashlib

fw = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/data/fw/rgx.sh"
d = open(fw, "rb").read()
n = len(d)
BS = 4096
info = d[n - BS:]
ver, hdrlen, num, entsize = struct.unpack_from("<IIII", info, 0)
bvnc, = struct.unpack_from("<Q", info, 16)
pagesize, flags = struct.unpack_from("<II", info, 24)
print(f"file={n} info_off={n-BS}")
print(f"ui32InfoVersion   = {ver}")
print(f"ui32HeaderLen     = {hdrlen}")
print(f"ui32LayoutEntryNum= {num}")
print(f"ui32LayoutEntrySize={entsize}")
print(f"ui64BVNC          = 0x{bvnc:016x}  (B={bvnc>>48} V={(bvnc>>32)&0xffff} N={(bvnc>>16)&0xffff} C={bvnc&0xffff})")
print(f"ui32FwPageSize    = {pagesize}")
print(f"ui32Flags         = 0x{flags:08x}")

# layout entries right after header
off = n - BS + hdrlen
for i in range(min(num, 8)):
    e = info[hdrlen + i*entsize: hdrlen + (i+1)*entsize]
    if len(e) < entsize:
        break
    eid, etype, base, maxs, alloc, aoff = struct.unpack_from("<IIIIII", e, 0)
    print(f"  entry[{i}] id={eid} type={etype} base=0x{base:08x} max={maxs} alloc={alloc} off={aoff}")

# look for other rgx.sh copies inside images on disk
roots = ["/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/dandelion-kernel",
         "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"]
print("\nsearching images for rgx.sh signature...")
sig = d[:32]
found = 0
for root in roots:
    for dp, _dd, fs in os.walk(root):
        for fn in fs:
            if fn.endswith((".img", ".zip", ".dat", ".sparse")):
                p = os.path.join(dp, fn)
                try:
                    if os.path.getsize(p) > 3_000_000_000:
                        continue
                    with open(p, "rb") as f:
                        while True:
                            b = f.read(1 << 20)
                            if not b:
                                break
                            k = b.find(sig)
                            if k >= 0:
                                print("sig hit:", p, "at", f.tell() - len(b) + k)
                                found += 1
                                break
                except OSError:
                    pass
        if found > 5:
            break
print("done, hits:", found)
