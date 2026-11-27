import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()
decl = "extern void mtk_pvr_dump_spm(const char *tag);\n"
# remove the misplaced declaration (inside NO_HARDWARE block)
s = s.replace("\n" + decl + "\n", "\n")
s = s.replace(decl, "")
# insert at file scope right before the function that uses it
anchor = "PVRSRV_ERROR RGXPostPowerState(IMG_HANDLE"
i = s.find(anchor)
if i < 0:
    raise SystemExit("anchor not found")
s = s[:i] + decl + "\n" + s[i:]
open(P, "w").write(s)
print("moved decl, count:", s.count(decl))
