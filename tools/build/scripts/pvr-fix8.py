R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = R + "/services/server/devices/rogue/rgxinit.c"
s = open(p).read()
old = "(int)RGX_IS_FEATURE_SUPPORTED(psDeviceNode->pvDevice, MIPS)"
new = "(int)RGX_IS_FEATURE_SUPPORTED((PVRSRV_RGXDEV_INFO *)psDeviceNode->pvDevice, MIPS)"
assert old in s
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("fixed")
