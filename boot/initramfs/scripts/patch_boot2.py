import struct

src = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-console.img"
dst = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-console2.img"

d = bytearray(open(src, "rb").read())
cmd = d[64:64+512].split(b"\x00", 1)[0].decode()
print("old:", cmd)

add = []
if "systemd.mask=dandelion-early-shell.service" not in cmd:
    add.append("systemd.mask=dandelion-early-shell.service")
if add:
    cmd = cmd + " " + " ".join(add)

new = cmd.encode() + b"\x00"
assert len(new) <= 512, "cmdline too long: %d" % len(new)
d[64:64+512] = b"\x00" * 512
d[64:64+len(new)] = new

open(dst, "wb").write(d)
print("new:", cmd)
print("len:", len(cmd))
