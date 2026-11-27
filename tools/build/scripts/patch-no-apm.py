import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "pvr_no_apm" in s:
    print("already patched")
    raise SystemExit(0)

anchor = 'static void pvr_maybe_move_prim(PVRSRV_RGXDEV_INFO *psDevInfo);\n'
i = s.find(anchor)
if i < 0:
    raise SystemExit("fwd decl anchor not found")

param = ("static int pvr_no_apm = 0;\n"
         "module_param(pvr_no_apm, int, 0644);\n"
         "MODULE_PARM_DESC(pvr_no_apm, \"clear RGXFWIF_INICFG_POW_RASCALDUST before FW boots\");\n\n")
s = s[:i] + param + s[i:]

# extend the early helper
a = "\tif (!pvr_prim_in_ccb || !psDevInfo->psRGXFWIfOsInit || !psDevInfo->psKernelCCBCtl)\n\t\treturn;\n"
j = s.find(a)
if j < 0:
    raise SystemExit("helper body anchor not found")
ins = ("\tif (pvr_no_apm && psDevInfo->psRGXFWIfFwSysData)\n"
       "\t{\n"
       "\t\tpsDevInfo->psRGXFWIfFwSysData->ui32ConfigFlags &=\n"
       "\t\t\t~(IMG_UINT32)RGXFWIF_INICFG_POW_RASCALDUST;\n"
       "\t\tpr_info(\"pvr-mtk: APM off, syscfg=%08x\\n\",\n"
       "\t\t        psDevInfo->psRGXFWIfFwSysData->ui32ConfigFlags);\n"
       "\t}\n\n")
s = s[:j] + ins + s[j:]

# also call the helper when only pvr_no_apm is set (it currently returns early)
s = s.replace("\tif (!pvr_prim_in_ccb || !psDevInfo->psRGXFWIfOsInit || !psDevInfo->psKernelCCBCtl)\n\t\treturn;\n",
              "\tif (!pvr_prim_in_ccb && !pvr_no_apm)\n\t\treturn;\n"
              "\tif (!psDevInfo->psRGXFWIfOsInit || !psDevInfo->psKernelCCBCtl)\n\t\treturn;\n")

open(P, "w").write(s)
print("pvr_no_apm added")
