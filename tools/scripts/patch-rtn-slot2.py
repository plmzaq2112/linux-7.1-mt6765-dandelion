import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "sync=%u rtn=%08x" in s:
    print("already patched")
    raise SystemExit(0)

old = 'sync=%u fwaddr=%08x cpuva=%px kccb=%u/%u slot=%u pow=%u'
new = 'sync=%u rtn=%08x fwaddr=%08x cpuva=%px kccb=%u/%u slot=%u pow=%u'
n = s.count(old)
if n != 1:
    raise SystemExit("print format count=%d" % n)
s = s.replace(old, new)

old2 = "\t\ttag, ui32Sync,\n"
n2 = s.count(old2)
if n2 != 1:
    raise SystemExit("arg anchor count=%d" % n2)
s = s.replace(old2,
    "\t\ttag, ui32Sync,\n"
    "\t\t(psDevInfo->pui32KernelCCBRtnSlots != NULL) ? psDevInfo->pui32KernelCCBRtnSlots[ui32Slot] : 0xDEADBEEFu,\n")

open(P, "w").write(s)
print("rtn slot print added")
