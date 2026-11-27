import struct, subprocess, os, sys, gzip, io

img = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/dist/images/boot-dev-now.img"
d = open(img, "rb").read(4096)
magic = d[:8]
kernel_size = struct.unpack("<I", d[8:12])[0]
ramdisk_size = struct.unpack("<I", d[16:20])[0]
page = 2048
kaddr = 0x40080000
raddr = 0x51b00000
taddr = 0x47880000
print("magic", magic, "kernel", kernel_size, "ramdisk", ramdisk_size)

page_size = 2048
kernel_off = page_size
ramdisk_off = kernel_off + ((kernel_size + page_size - 1) // page_size) * page_size
print("kernel_off", hex(kernel_off), "ramdisk_off", hex(ramdisk_off))

full = open(img, "rb").read()
rd = full[ramdisk_off:ramdisk_off + ramdisk_size]
print("ramdisk bytes", len(rd), "magic", rd[:4].hex())

# try gzip
try:
    data = gzip.decompress(rd)
    print("gzip ok,", len(data), "bytes")
    open("/tmp/initramfs.cpio", "wb").write(data)
except Exception as e:
    print("gzip fail", e)
    # maybe lz4
    open("/tmp/initramfs.raw", "wb").write(rd)
