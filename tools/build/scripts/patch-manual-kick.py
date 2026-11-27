import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "after-kick" in s:
    print("already patched")
    raise SystemExit(0)

anchor = "\t/* Wait for GPU to finish current workload */\n"
i = s.find(anchor)
if i < 0:
    raise SystemExit("anchor not found")

ins = (
    "\tpr_info(\"pvr-mtk: after-send kccb w=%u r=%u\\n\",\n"
    "\t        psDevInfo->psKernelCCBCtl->ui32WriteOffset,\n"
    "\t        psDevInfo->psKernelCCBCtl->ui32ReadOffset);\n"
    "\t/* manual GP kick: MTS_SCHEDULE = DM_GP */\n"
    "\tOSWriteHWReg32(psDevInfo->pvRegsBaseKM, 0xB00, RGXFWIF_DM_GP);\n"
    "\tmdelay(20);\n"
    "\tpr_info(\"pvr-mtk: after-kick kccb w=%u r=%u\\n\",\n"
    "\t        psDevInfo->psKernelCCBCtl->ui32WriteOffset,\n"
    "\t        psDevInfo->psKernelCCBCtl->ui32ReadOffset);\n\n") + anchor

s = s[:i] + ins + s[i + len(anchor):]
open(P, "w").write(s)
print("patched manual kick")
