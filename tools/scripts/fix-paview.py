import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(p).read()

a = s.find("\tIMG_UINT32 ui32PaView = 0;\n")
b = s.find("\tif (psDevInfo->psPowSyncPrim && psDevInfo->psPowSyncPrim->pui32LinAddr)\n\t\tui32Sync", a)
if a < 0 or b < 0:
    raise SystemExit("markers not found a=%d b=%d" % (a, b))
s = s[:a] + "\tIMG_UINT32 ui32PaView = 0;\n\n" + s[b:]
open(p, "w").write(s)
print("cleaned")
