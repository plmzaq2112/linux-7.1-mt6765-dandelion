import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "pvr-mtk: conn fw=" in s:
    print("already patched")
    raise SystemExit(0)

a = '\tpr_info("pvr-mtk: forced-idle sent: kccb w=%u r=%u slot=%u\\n",\n'
i = s.find(a)
if i < 0:
    raise SystemExit("anchor not found")

ins = ('\tpr_info("pvr-mtk: conn fw=%u os=%u fwtok=%08x ostok=%08x mts=%08x\\n",\n'
       '\t        (unsigned)psDevInfo->psRGXFWIfConnectionCtl->eConnectionFwState,\n'
       '\t        (unsigned)psDevInfo->psRGXFWIfConnectionCtl->eConnectionOsState,\n'
       '\t        psDevInfo->psRGXFWIfConnectionCtl->ui32AliveFwToken,\n'
       '\t        psDevInfo->psRGXFWIfConnectionCtl->ui32AliveOsToken,\n'
       '\t        OSReadHWReg32(psDevInfo->pvRegsBaseKM, 0xB00));\n')

s = s[:i] + ins + s[i:]
open(P, "w").write(s)
print("patched connection diagnostics")
