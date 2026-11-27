import os
p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(p).read()

# 1) move the extern declaration up (before first use)
s = s.replace("\nextern IMG_UINT32 g_pvrFwTraceLimit;\n", "\n")
anchor = 'MODULE_PARM_DESC(pvr_fwtrace, "enable FW trace logging and dump FW trace around POW");\n'
if "extern IMG_UINT32 g_pvrFwTraceLimit;" not in s:
    s = s.replace(anchor, anchor + "\nextern IMG_UINT32 g_pvrFwTraceLimit;\n", 1)

# 2) IMG_NULL not defined in this file
s = s.replace("IMG_NULL", "NULL")

open(p, "w").write(s)
print("extern count:", s.count("extern IMG_UINT32 g_pvrFwTraceLimit;"))
print("IMG_NULL left:", s.count("IMG_NULL"))
