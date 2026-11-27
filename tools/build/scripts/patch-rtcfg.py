import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "RT cfg=" in s:
    print("already patched")
    raise SystemExit(0)

anchor = '\t\tpr_info("pvr-mtk: OSINIT osdata=%08x rtn=%08x fwccbctl=%08x fwccb=%08x\\n",\n'
i = s.find(anchor)
if i < 0:
    raise SystemExit("anchor not found")

ins = ('\t\tpr_info("pvr-mtk: RT cfg=%08x pm=%u clk=%u dusts=%u syscfg=%08x syscfgx=%08x\\n",\n'
       '\t\t        psDevInfo->psRGXFWIfRuntimeCfg->ui32RuntimeCfgFlags,\n'
       '\t\t        psDevInfo->psRGXFWIfRuntimeCfg->ui32ActivePMLatencyms,\n'
       '\t\t        psDevInfo->psRGXFWIfRuntimeCfg->ui32CoreClockSpeed,\n'
       '\t\t        psDevInfo->psRGXFWIfRuntimeCfg->ui32DefaultDustsNumInit,\n'
       '\t\t        psDevInfo->psRGXFWIfFwSysData ? psDevInfo->psRGXFWIfFwSysData->ui32ConfigFlags : 0U,\n'
       '\t\t        psDevInfo->psRGXFWIfFwSysData ? psDevInfo->psRGXFWIfFwSysData->ui32ConfigFlagsExt : 0U);\n')

s = s[:i] + ins + s[i:]
open(P, "w").write(s)
print("RT cfg print added")
