import struct

SRC = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-audio9.img"
DST = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-audio10.img"

d = bytearray(open(SRC, "rb").read())
old = d[64:64+512].split(b"\x00", 1)[0].decode()
print("old:", old)

cmd = old.replace(" console=ttyGS0,115200", "")
print("new:", cmd)

nb = cmd.encode() + b"\x00"
assert len(nb) <= 512
d[64:64+512] = b"\x00" * 512
d[64:64+len(nb)] = nb
open(DST, "wb").write(d)
print("wrote", len(d), "bytes")
