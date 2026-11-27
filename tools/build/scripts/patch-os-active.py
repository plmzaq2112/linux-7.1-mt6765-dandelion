import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "pvr_os_active" in s:
    print("already patched")
    raise SystemExit(0)

# param declaration right before the function
fn = "PVRSRV_ERROR RGXForcedIdleRequest(IMG_HANDLE hDevHandle, IMG_BOOL bDeviceOffPermitted)"
i = s.find(fn)
if i < 0:
    raise SystemExit("function not found")
param = ("static int pvr_os_active = 0;\n"
         "module_param(pvr_os_active, int, 0644);\n"
         "MODULE_PARM_DESC(pvr_os_active, \"set OS connection state ACTIVE before POW (diagnostic)\");\n\n")
s = s[:i] + param + s[i:]

# set it right after the GUEST early-return inside the function
anchor = "\tPVRSRV_VZ_RET_IF_MODE(GUEST, PVRSRV_OK);\n"
j = s.find(anchor, i + len(param))
if j < 0:
    raise SystemExit("body anchor not found")
ins = anchor + (
    "\n\tif (pvr_os_active) {\n"
    "\t\tpsDevInfo->psRGXFWIfConnectionCtl->eConnectionOsState = RGXFW_CONNECTION_OS_ACTIVE;\n"
    "\t\tpr_info(\"pvr-mtk: OS state forced to ACTIVE\\n\");\n"
    "\t}\n")
s = s[:j] + ins + s[j + len(anchor):]

open(P, "w").write(s)
print("pvr_os_active added")
