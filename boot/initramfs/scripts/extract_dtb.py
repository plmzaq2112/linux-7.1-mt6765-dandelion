import struct, sys

src = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-console2.img"
d = open(src, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
hv = struct.unpack_from("<I", d, 40)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
ds = struct.unpack_from("<I", d, 1648)[0]
au = lambda x, p: ((x + p - 1) // p) * p
kd = page
rd = kd + au(ks, page)
dt = rd + au(rs, page)
blob = d[dt:dt+ds]
open("/tmp/live.dtb", "wb").write(blob)
print("dtb size", ds, "magic", blob[:4].hex(), "totalsize", struct.unpack_from(">I", blob, 4)[0])
