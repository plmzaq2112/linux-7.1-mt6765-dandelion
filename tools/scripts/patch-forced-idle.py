import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "pvr-mtk: forced-idle" in s:
    print("already patched")
    raise SystemExit(0)

a1 = "\tpsFwSysData = psDevInfo->psRGXFWIfFwSysData;\n"
i1 = s.find(a1)
if i1 < 0:
    raise SystemExit("anchor1 not found")
ins1 = a1 + ('\tpr_info("pvr-mtk: forced-idle enter: pow=%u kccb w=%u r=%u\\n",\n'
             '\t        (unsigned)psFwSysData->ePowState,\n'
             '\t        psDevInfo->psKernelCCBCtl->ui32WriteOffset,\n'
             '\t        psDevInfo->psKernelCCBCtl->ui32ReadOffset);\n')
s = s[:i1] + ins1 + s[i1 + len(a1):]

a2 = "\t/* Wait for GPU to finish current workload */\n"
i2 = s.find(a2)
if i2 < 0:
    raise SystemExit("anchor2 not found")
ins2 = ('\tpr_info("pvr-mtk: forced-idle sent: kccb w=%u r=%u slot=%u\\n",\n'
        '\t        psDevInfo->psKernelCCBCtl->ui32WriteOffset,\n'
        '\t        psDevInfo->psKernelCCBCtl->ui32ReadOffset,\n'
        '\t        ui32CmdKCCBSlot);\n\n') + a2
s = s[:i2] + ins2 + s[i2 + len(a2):]

a3 = "\t\tRGXFWNotifyHostTimeout(psDevInfo);\n"
i3 = s.find(a3)
if i3 < 0:
    raise SystemExit("anchor3 not found")
ins3 = ('\t\tpr_info("pvr-mtk: forced-idle timeout: kccb w=%u r=%u\\n",\n'
        '\t\t        psDevInfo->psKernelCCBCtl->ui32WriteOffset,\n'
        '\t\t        psDevInfo->psKernelCCBCtl->ui32ReadOffset);\n') + a3
s = s[:i3] + ins3 + s[i3 + len(a3):]

open(P, "w").write(s)
print("patched forced-idle diagnostics")
