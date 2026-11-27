import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "static void pvr_maybe_move_prim(PVRSRV_RGXDEV_INFO *psDevInfo);" in s:
    print("already")
    raise SystemExit(0)

a = "#if defined(LINUX)\n#include <linux/vmalloc.h>\n#include <linux/mm.h>\n#endif\n"
i = s.find(a)
if i < 0:
    raise SystemExit("include anchor not found")
s = s[:i + len(a)] + "\nstatic void pvr_maybe_move_prim(PVRSRV_RGXDEV_INFO *psDevInfo);\n" + s[i + len(a):]
open(P, "w").write(s)
print("forward decl added")
