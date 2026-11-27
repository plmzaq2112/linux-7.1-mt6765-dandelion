import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

# 1) remove the two misplaced calls (they are outside RGXForcedIdleRequest)
mis1 = '\t\tpvr_pow_snap(psDevInfo, "before", &sPowCmd, 0);\n'
mis2 = '\t\tpvr_pow_snap(psDevInfo, "poll", &sPowCmd, ui32CmdKCCBSlot);\n'

fn = s.find("PVRSRV_ERROR RGXForcedIdleRequest(IMG_HANDLE hDevHandle, IMG_BOOL bDeviceOffPermitted)")
if fn < 0:
    raise SystemExit("function not found")

head, tail = s[:fn], s[fn:]
head = head.replace(mis1, "").replace(mis2, "")

# 2) insert "before" before the SyncPrimSet inside the function
a1 = "\teError = SyncPrimSet(psDevInfo->psPowSyncPrim, 0);\n"
i1 = tail.find(a1)
if i1 < 0:
    raise SystemExit("SyncPrimSet in function not found")
tail = tail[:i1] + '\tpvr_pow_snap(psDevInfo, "before", &sPowCmd, 0);\n' + tail[i1:]

# 3) insert "poll" after the forced-idle poll
p = tail.find("psDevInfo->psPowSyncPrim->pui32LinAddr,")
q = tail.find("0x1, 0xFFFFFFFF);", p)
if p < 0 or q < 0:
    raise SystemExit("poll anchor not found")
q = tail.find("\n", q) + 1
tail = tail[:q] + '\t\tpvr_pow_snap(psDevInfo, "poll", &sPowCmd, ui32CmdKCCBSlot);\n' + tail[q:]

open(P, "w").write(head + tail)
print("fixed placement")
