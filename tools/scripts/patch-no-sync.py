import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxfwutils.c")
s = open(P).read()

if "pvr_no_sync" in s:
    print("already patched")
    raise SystemExit(0)

anchor = "PVRSRV_ERROR IMG_CALLCONV RGXPollForGPCommandCompletion(PVRSRV_DEVICE_NODE  *psDevNode,"
i = s.find(anchor)
if i < 0:
    raise SystemExit("function anchor not found")

param = ("static int pvr_no_sync = 0;\n"
         "module_param(pvr_no_sync, int, 0644);\n"
         "MODULE_PARM_DESC(pvr_no_sync, \"treat GP command completion timeouts as success (bring-up)\");\n\n")
s = s[:i] + param + s[i:]

# after the retry loop, before the error print
tail = "\tif (eError != PVRSRV_OK)\n\t{\n\t\tPVR_DPF((PVR_DBG_ERROR, \"%s: Failed! Error(%s) CPU linear address(%p) Expected value(%u)\","
j = s.find(tail, i + len(param))
if j < 0:
    raise SystemExit("tail anchor not found")

ins = ("\tif (eError == PVRSRV_ERROR_TIMEOUT && pvr_no_sync)\n"
       "\t{\n"
       "\t\tpr_info(\"pvr-mtk: no-sync: GP poll timeout treated as complete\\n\");\n"
       "\t\teError = PVRSRV_OK;\n"
       "\t}\n\n")
s = s[:j] + ins + s[j:]
open(P, "w").write(s)
print("pvr_no_sync added")
