import struct

src = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-current.img"
dst = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-console.img"

d = bytearray(open(src, "rb").read())
cmd = d[64:64+512].split(b"\x00", 1)[0].decode()
print("old:", cmd)

if "console=ttyGS0" not in cmd:
    cmd = cmd + " console=ttyGS0,115200"

new = cmd.encode() + b"\x00"
assert len(new) <= 512, "cmdline too long"
d[64:64+512] = b"\x00" * 512
d[64:64+len(new)] = new

open(dst, "wb").write(d)
print("new:", cmd)
print("len:", len(cmd), "wrote", len(d), "bytes")

# verify
v = open(dst, "rb").read()
print("verify:", v[64:64+512].split(b"\x00",1)[0].decode())
print("same size:", len(v) == 67108864)
