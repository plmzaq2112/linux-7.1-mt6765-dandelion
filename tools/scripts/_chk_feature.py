import sys
p = r"/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/out/drivers/misc/pvr/ddk/pvrsrvkm.ko"
d = open(p, "rb").read()
for name, val in [("bus36", 0x0008d28253100100), ("bus32", 0x0008d28353100100)]:
    b = val.to_bytes(8, "little")
    print(name, hex(val), "count", d.count(b))
