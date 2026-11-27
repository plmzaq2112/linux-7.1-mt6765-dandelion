R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = R + "/services/server/devices/rogue/rgxinit.c"
s = open(p).read()
old = """\tpr_info("pvr-mtk: FW mem '%s' size=%llu align_log2=%u (MIPS=%d)\\n",
\t        pszText, (unsigned long long)ui32Size, (unsigned int)uiLog2Align,
\t        (int)RGX_IS_FEATURE_SUPPORTED((PVRSRV_RGXDEV_INFO *)psDeviceNode->pvDevice, MIPS));
"""
new = """\tpr_info("pvr-mtk: FW mem '%s' size=%llu align_log2=%u\\n",
\t        pszText, (unsigned long long)ui32Size, (unsigned int)uiLog2Align);
"""
assert old in s, "pattern not found"
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("simplified")
