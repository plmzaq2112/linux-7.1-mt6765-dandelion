import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "sPowerSync" in s:
    print("already patched")
    raise SystemExit(0)

anchor = '\t\treturn PVRSRV_OK;\n\t}\n'
# find the skip_fidle block's return
i = s.find("if (pvr_skip_fidle) {")
if i < 0:
    raise SystemExit("skip block not found")
j = s.find(anchor, i)
if j < 0:
    raise SystemExit("return anchor not found")

ins = ('\t\tpr_info("pvr-mtk: prim fwaddr=%08x cpuva=%px\\n",\n'
       '\t\t        psDevInfo->psRGXFWIfFwOsData->sPowerSync.ui32Addr,\n'
       '\t\t        psDevInfo->psPowSyncPrim->pui32LinAddr);\n')

s = s[:j] + ins + s[j:]
open(P, "w").write(s)
print("patched prim addresses")
