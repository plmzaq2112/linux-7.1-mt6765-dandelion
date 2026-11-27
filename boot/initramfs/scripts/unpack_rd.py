import struct, os, json

SRC = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-console2.img"
OUT = "/tmp/db"

os.makedirs(OUT, exist_ok=True)
d = open(SRC, "rb").read()

page = struct.unpack_from("<I", d, 36)[0]
hv = struct.unpack_from("<I", d, 40)[0]
ksize = struct.unpack_from("<I", d, 8)[0]
rsize = struct.unpack_from("<I", d, 16)[0]
dsize = struct.unpack_from("<I", d, 1648)[0] if hv >= 2 else 0


def au(x, p):
    return ((x + p - 1) // p) * p


k_off = page
rd_off = k_off + au(ksize, page)
dtb_off = rd_off + au(rsize, page)

hdr = d[:page]
kernel = d[k_off:k_off + ksize]
ramdisk = d[rd_off:rd_off + rsize]
dtb = d[dtb_off:dtb_off + dsize]

open(os.path.join(OUT, "header.bin"), "wb").write(hdr)
open(os.path.join(OUT, "kernel.bin"), "wb").write(kernel)
open(os.path.join(OUT, "ramdisk.gz"), "wb").write(ramdisk)
open(os.path.join(OUT, "dtb.bin"), "wb").write(dtb)

meta = {
    "page": page, "header_version": hv,
    "kernel_size": ksize, "ramdisk_size": rsize, "dtb_size": dsize,
    "orig_total": len(d),
    "ramdisk_magic": ramdisk[:2].hex(),
}
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), indent=1)
print(json.dumps(meta, indent=1))
