R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = R + "/services/server/devices/rogue/rgxinit.c"
s = open(p).read()
old = 'pr_info("pvr-mtk: fw code DevVAddr=%llx (want %llx), data DevVAddr pending",\n\t         psDevInfo->sFWCodeDevVAddrBase.uiAddr,'
new = 'pr_info("pvr-mtk: fw code DevVAddr=%llx (want %llx)\\n",\n\t         (unsigned long long)psDevInfo->sFWCodeDevVAddrBase.uiAddr,'
assert old in s, "pattern not found"
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("done")
