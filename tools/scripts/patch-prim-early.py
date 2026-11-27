import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "pvr_maybe_move_prim" in s:
    print("already patched")
    raise SystemExit(0)

# helper after the module params
anchor = "MODULE_PARM_DESC(pvr_prim_in_ccb, \"place the POW sync prim inside the KCCB ctl page (diagnostic)\");\n"
i = s.find(anchor)
if i < 0:
    raise SystemExit("param anchor not found")

helper = anchor + (
    "\nstatic void pvr_maybe_move_prim(PVRSRV_RGXDEV_INFO *psDevInfo)\n"
    "{\n"
    "\tIMG_UINT32 ui32Fw;\n"
    "\tif (!pvr_prim_in_ccb || !psDevInfo->psRGXFWIfOsInit || !psDevInfo->psKernelCCBCtl)\n"
    "\t\treturn;\n"
    "\tui32Fw = psDevInfo->psRGXFWIfOsInit->psKernelCCBCtl.ui32Addr + 0x100;\n"
    "\tpsDevInfo->psRGXFWIfFwOsData->sPowerSync.ui32Addr = ui32Fw;\n"
    "\tpsDevInfo->psPowSyncPrim->pui32LinAddr =\n"
    "\t\t(volatile IMG_UINT32 __iomem *)((IMG_UINT8 *)psDevInfo->psKernelCCBCtl + 0x100);\n"
    "\tpr_info(\"pvr-mtk: prim->ccb page (early) fw=%08x va=%px\\n\",\n"
    "\t        ui32Fw, psDevInfo->psPowSyncPrim->pui32LinAddr);\n"
    "}\n")
s = s[:i] + helper + s[i + len(anchor):]

# call it before RGXDoStart in RGXPostPowerState
a = "\t\t\teError = RGXDoStart(psDeviceNode);\n"
j = s.find(a)
if j < 0:
    raise SystemExit("RGXDoStart anchor not found")
s = s[:j] + "\t\t\tpvr_maybe_move_prim(psDevInfo);\n" + s[j:]

open(P, "w").write(s)
print("early override added")
