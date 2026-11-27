import os

R = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk")
UTIL = os.path.join(R, "services/server/devices/rogue/rgxfwutils.c")
PWR = os.path.join(R, "services/server/devices/rogue/rgxpower.c")

# 1) turn the util-local static param into a module-wide flag
s = open(UTIL).read()
old = ("static int pvr_no_sync = 0;\n"
       "module_param(pvr_no_sync, int, 0644);\n"
       "MODULE_PARM_DESC(pvr_no_sync, \"treat GP command completion timeouts as success (bring-up)\");\n")
new = ("IMG_BOOL g_pvrNoSync = IMG_FALSE;\n"
       "module_param_named(pvr_no_sync, g_pvrNoSync, bool, 0644);\n"
       "MODULE_PARM_DESC(pvr_no_sync, \"treat GP poll timeouts / FW state checks as success (bring-up)\");\n")
if old in s:
    s = s.replace(old, new)
    open(UTIL, "w").write(s)
    print("rgxfwutils: flag exported")
elif "g_pvrNoSync" in s:
    print("rgxfwutils: already")
else:
    raise SystemExit("util anchor not found")

# 2) use it in the forced-idle state check
s = open(PWR).read()
if "g_pvrNoSync" in s:
    print("rgxpower: already")
else:
    a = "PVRSRV_ERROR RGXForcedIdleRequest(IMG_HANDLE hDevHandle, IMG_BOOL bDeviceOffPermitted)"
    i = s.find(a)
    if i < 0:
        raise SystemExit("power fn not found")
    s = s[:i] + "extern IMG_BOOL g_pvrNoSync;\n\n" + s[i:]

    chk = "\tif (psFwSysData->ePowState != RGXFWIF_POW_FORCED_IDLE)\n"
    j = s.find(chk)
    if j < 0:
        raise SystemExit("state check not found")
    s = s.replace(chk, "\tif (!g_pvrNoSync && psFwSysData->ePowState != RGXFWIF_POW_FORCED_IDLE)\n", 1)
    open(PWR, "w").write(s)
    print("rgxpower: state check relaxed")
