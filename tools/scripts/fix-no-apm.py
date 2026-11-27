import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

old = "\tif (!pvr_prim_in_ccb && !pvr_no_apm)\n\t\treturn;\n\tif (!psDevInfo->psRGXFWIfOsInit || !psDevInfo->psKernelCCBCtl)\n\t\treturn;\n"
new = "\tif (!pvr_prim_in_ccb)\n\t\treturn;\n\tif (!psDevInfo->psRGXFWIfOsInit || !psDevInfo->psKernelCCBCtl)\n\t\treturn;\n"
if old not in s:
    print("anchor not found (maybe already fixed)")
    raise SystemExit(0)
s = s.replace(old, new, 1)
open(P, "w").write(s)
print("prim move now gated by pvr_prim_in_ccb only")
