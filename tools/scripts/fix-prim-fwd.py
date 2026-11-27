import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

decl = "static void pvr_maybe_move_prim(PVRSRV_RGXDEV_INFO *psDevInfo);\n"
s = s.replace(decl, "", 1)

anchor = '#include "rgxdefs_km.h"\n'
i = s.find(anchor)
if i < 0:
    raise SystemExit("include anchor not found")
s = s[:i + len(anchor)] + "\n" + decl + s[i + len(anchor):]
open(P, "w").write(s)
print("forward decl moved")
