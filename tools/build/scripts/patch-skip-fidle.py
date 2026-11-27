import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "pvr_skip_fidle" in s:
    print("already patched")
    raise SystemExit(0)

anchor = "PVRSRV_ERROR RGXForcedIdleRequest(IMG_HANDLE hDevHandle, IMG_BOOL bDeviceOffPermitted)\n{\n"
i = s.find(anchor)
if i < 0:
    raise SystemExit("function not found")

param = ("static int pvr_skip_fidle = 0;\n"
         "module_param(pvr_skip_fidle, int, 0644);\n"
         "MODULE_PARM_DESC(pvr_skip_fidle, \"skip the forced-idle KCCB request (diagnostic)\");\n\n")

body_anchor = "\tPVRSRV_VZ_RET_IF_MODE(GUEST, PVRSRV_OK);\n"
j = s.find(body_anchor, i)
if j < 0:
    raise SystemExit("body anchor not found")

ins = body_anchor + (
    "\n\tif (pvr_skip_fidle) {\n"
    "\t\tpr_info(\"pvr-mtk: skip-fidle conn fw=%u os=%u fwtok=%08x ostok=%08x mts=%08x kccb w=%u r=%u pow=%u\\n\",\n"
    "\t\t        (unsigned)psDevInfo->psRGXFWIfConnectionCtl->eConnectionFwState,\n"
    "\t\t        (unsigned)psDevInfo->psRGXFWIfConnectionCtl->eConnectionOsState,\n"
    "\t\t        psDevInfo->psRGXFWIfConnectionCtl->ui32AliveFwToken,\n"
    "\t\t        psDevInfo->psRGXFWIfConnectionCtl->ui32AliveOsToken,\n"
    "\t\t        OSReadHWReg32(psDevInfo->pvRegsBaseKM, 0xB00),\n"
    "\t\t        psDevInfo->psKernelCCBCtl->ui32WriteOffset,\n"
    "\t\t        psDevInfo->psKernelCCBCtl->ui32ReadOffset,\n"
    "\t\t        psDevInfo->psRGXFWIfFwSysData ? (unsigned)psDevInfo->psRGXFWIfFwSysData->ePowState : 999U);\n"
    "\t\treturn PVRSRV_OK;\n"
    "\t}\n")

s = s[:i] + param + s[i:]
j = s.find(body_anchor, i + len(param))
s = s[:j] + ins + s[j + len(body_anchor):]

open(P, "w").write(s)
print("patched pvr_skip_fidle")
