import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "OSINIT kccbctl" in s:
    print("already patched")
    raise SystemExit(0)

anchor = '\t\tpr_info("pvr-mtk: prim fwaddr=%08x cpuva=%px\\n",\n'
i = s.find(anchor)
if i < 0:
    raise SystemExit("prim print anchor not found")

ins = ('\t\tpr_info("pvr-mtk: OSINIT kccbctl=%08x kccb=%08x cmdsize=%u wrapmask=%u\\n",\n'
       '\t\t        psDevInfo->psRGXFWIfOsInit->psKernelCCBCtl.ui32Addr,\n'
       '\t\t        psDevInfo->psRGXFWIfOsInit->psKernelCCB.ui32Addr,\n'
       '\t\t        psDevInfo->psKernelCCBCtl->ui32CmdSize,\n'
       '\t\t        psDevInfo->psKernelCCBCtl->ui32WrapMask);\n')

s = s[:i] + ins + s[i:]
open(P, "w").write(s)
print("added OSINIT kccb print")
