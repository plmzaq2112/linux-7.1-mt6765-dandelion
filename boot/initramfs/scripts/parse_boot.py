import struct, sys

p = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-current.img"
d = open(p, "rb").read()

page = struct.unpack_from("<I", d, 36)[0]
hv = struct.unpack_from("<I", d, 40)[0]
ksize = struct.unpack_from("<I", d, 8)[0]
rsize = struct.unpack_from("<I", d, 16)[0]
cmd = d[64:64+512].split(b"\x00", 1)[0].decode(errors="replace")

print("magic:", d[:8])
print("page=%d header_version=%d kernel_size=%d ramdisk_size=%d" % (page, hv, ksize, rsize))
print("cmdline(%d): %s" % (len(cmd), cmd))

# dtb info for v2
if hv >= 2:
    dsz = struct.unpack_from("<I", d, 1648)[0]
    daddr = struct.unpack_from("<Q", d, 1652)[0]
    print("dtb_size=%d dtb_addr=0x%x" % (dsz, daddr))
