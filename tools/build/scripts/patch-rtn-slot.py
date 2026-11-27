import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "rtn=%08x" in s:
    print("already patched")
    raise SystemExit(0)

old = '\tpr_info("pvr-mtk: POW[%s] sync=%u fwaddr=%08x cpuva=%px kccb=%u/%u slot=%u pow=%u hwr=%08x fwirq=%u faults=%u\\n",\n'
new = ('\tpr_info("pvr-mtk: POW[%s] sync=%u rtn=%08x fwaddr=%08x cpuva=%px kccb=%u/%u slot=%u pow=%u hwr=%08x fwirq=%u faults=%u\\n",\n')
i = s.find(old)
if i < 0:
    raise SystemExit("print anchor not found")
s = s[:i] + new + s[i + len(old):]

# add the rtn argument after ui32Sync
old2 = "\t\ttag, ui32Sync,\n"
new2 = ("\t\ttag, ui32Sync,\n"
        "\t\t(psDevInfo->pui32KernelCCBRtnSlots != NULL) ? psDevInfo->pui32KernelCCBRtnSlots[ui32Slot] : 0xDEADBEEFu,\n")
j = s.find(old2)
if j < 0:
    raise SystemExit("arg anchor not found")
s = s[:j] + new2 + s[j + len(old2):]

open(P, "w").write(s)
print("rtn slot print added")
