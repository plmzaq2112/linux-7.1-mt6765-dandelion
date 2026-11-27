import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "pvr_prim_in_ccb" in s:
    print("already patched")
    raise SystemExit(0)

anchor = "extern int g_pvrNoSync;\n\n"
i = s.find(anchor)
if i < 0:
    raise SystemExit("extern anchor not found")

param = ("static int pvr_prim_in_ccb = 0;\n"
         "module_param(pvr_prim_in_ccb, int, 0644);\n"
         "MODULE_PARM_DESC(pvr_prim_in_ccb, \"place the POW sync prim inside the KCCB ctl page (diagnostic)\");\n\n")
s = s[:i] + param + s[i:]

# insert the remap right before SyncPrimSet(0) inside the forced-idle function
fn = "PVRSRV_ERROR RGXForcedIdleRequest(IMG_HANDLE hDevHandle, IMG_BOOL bDeviceOffPermitted)"
fi = s.find(fn)
if fi < 0:
    raise SystemExit("fn not found")

a1 = "\teError = SyncPrimSet(psDevInfo->psPowSyncPrim, 0);\n"
j = s.find(a1, fi)
if j < 0:
    raise SystemExit("SyncPrimSet not found")

ins = ("\tif (pvr_prim_in_ccb)\n"
       "\t{\n"
       "\t\tIMG_UINT32 ui32Fw = psDevInfo->psRGXFWIfOsInit->psKernelCCBCtl.ui32Addr + 0x100;\n"
       "\t\tpsDevInfo->psRGXFWIfFwOsData->sPowerSync.ui32Addr = ui32Fw;\n"
       "\t\tpsDevInfo->psPowSyncPrim->pui32LinAddr =\n"
       "\t\t\t(volatile IMG_UINT32 __iomem *)((IMG_UINT8 *)psDevInfo->psKernelCCBCtl + 0x100);\n"
       "\t\tpr_info(\"pvr-mtk: prim->ccb page fw=%08x va=%px\\n\",\n"
       "\t\t        ui32Fw, psDevInfo->psPowSyncPrim->pui32LinAddr);\n"
       "\t}\n\n")

s = s[:j] + ins + s[j:]
open(P, "w").write(s)
print("pvr_prim_in_ccb added")
