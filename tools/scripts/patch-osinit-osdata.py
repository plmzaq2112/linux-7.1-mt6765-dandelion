import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "OSINIT osdata=" in s:
    print("already patched")
    raise SystemExit(0)

anchor = '\t\tpr_info("pvr-mtk: OSINIT kccbctl=%08x kccb=%08x cmdsize=%u wrapmask=%u\\n",\n'
i = s.find(anchor)
if i < 0:
    raise SystemExit("anchor not found")

ins = ('\t\tpr_info("pvr-mtk: OSINIT osdata=%08x rtn=%08x fwccbctl=%08x fwccb=%08x\\n",\n'
       '\t\t        psDevInfo->psRGXFWIfOsInit->sFwOsData.ui32Addr,\n'
       '\t\t        psDevInfo->psRGXFWIfOsInit->psKernelCCBRtnSlots.ui32Addr,\n'
       '\t\t        psDevInfo->psRGXFWIfOsInit->psFirmwareCCBCtl.ui32Addr,\n'
       '\t\t        psDevInfo->psRGXFWIfOsInit->psFirmwareCCB.ui32Addr);\n')

s = s[:i] + ins + s[i:]
open(P, "w").write(s)
print("OSINIT osdata print added")
