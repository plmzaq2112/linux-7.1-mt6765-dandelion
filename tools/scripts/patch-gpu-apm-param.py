import os

P = os.path.expanduser(
    "~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/system/rogue/rgx_mtk/pvr_platform_mt6765.c")
s = open(P).read()

if "pvr_apm" in s:
    print("already patched")
    raise SystemExit(0)

# 1) module param + early return in pvr_mtk_init_apm()
old = "static void pvr_mtk_init_apm(void)\n{"
new = ("static int pvr_apm = 0;\n"
       "module_param(pvr_apm, int, 0644);\n"
       "MODULE_PARM_DESC(pvr_apm, \"program MTK HW APM registers (may power-gate MFG_CORE0)\");\n"
       "\n"
       "static void pvr_mtk_init_apm(void)\n"
       "{\n"
       "\tif (!pvr_apm)\n"
       "\t\treturn;")
if old not in s:
    raise SystemExit("init_apm anchor not found")
s = s.replace(old, new, 1)

open(P, "w").write(s)
print("patched pvr_apm param")
