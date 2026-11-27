import os

R = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk")
UTIL = os.path.join(R, "services/server/devices/rogue/rgxfwutils.c")
PWR = os.path.join(R, "services/server/devices/rogue/rgxpower.c")

# --- rgxfwutils.c: use int flag, fix usage name ---
s = open(UTIL).read()
s = s.replace("IMG_BOOL g_pvrNoSync = IMG_FALSE;\nmodule_param_named(pvr_no_sync, g_pvrNoSync, bool, 0644);",
              "int g_pvrNoSync = 0;\nmodule_param_named(pvr_no_sync, g_pvrNoSync, int, 0644);")
s = s.replace("&& pvr_no_sync)", "&& g_pvrNoSync)")
open(UTIL, "w").write(s)

# --- rgxpower.c: fix placement ---
s = open(PWR).read()
# revert the wrong one
s = s.replace("\tif (!g_pvrNoSync && psFwSysData->ePowState != RGXFWIF_POW_FORCED_IDLE)\n",
              "\tif (psFwSysData->ePowState != RGXFWIF_POW_FORCED_IDLE)\n")
# remove misplaced extern
s = s.replace("extern IMG_BOOL g_pvrNoSync;\n\n", "")

fn = "PVRSRV_ERROR RGXForcedIdleRequest(IMG_HANDLE hDevHandle, IMG_BOOL bDeviceOffPermitted)"
i = s.find(fn)
if i < 0:
    raise SystemExit("fn not found")
s = s[:i] + "extern int g_pvrNoSync;\n\n" + s[i:]

# wrap the check inside the function (first occurrence after fn start)
chk = "\tif (psFwSysData->ePowState != RGXFWIF_POW_FORCED_IDLE)\n"
j = s.find(chk, i + 40)
if j < 0:
    raise SystemExit("in-function check not found")
s = s[:j] + "\tif (!g_pvrNoSync && psFwSysData->ePowState != RGXFWIF_POW_FORCED_IDLE)\n" + s[j + len(chk):]

open(PWR, "w").write(s)
print("fixed")
