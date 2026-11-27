R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = R + "/services/server/devices/rogue/rgxfwutils.h"
s = open(p).read()

old = """\teError = DevmemAllocateExportable(psDeviceNode,
\t\t\t\t\t\t\t\t\t  uiSize,
\t\t\t\t\t\t\t\t\t  uiAlign,
\t\t\t\t\t\t\t\t\t  RGX_IS_FEATURE_SUPPORTED(psDevInfo, MIPS) ?
\t\t\t\t\t\t\t\t\t  ExactLog2(uiAlign) :
\t\t\t\t\t\t\t\t\t  DevmemGetHeapLog2PageSize(psFwHeap),
\t\t\t\t\t\t\t\t\t  uiFlags,
\t\t\t\t\t\t\t\t\t  pszText,
\t\t\t\t\t\t\t\t\t  ppsMemDescPtr);"""
new = """\t/* Always use the requested alignment as the allocation page size.
\t * For MIPS this gives 64K pages -> CMA (physically contiguous, low memory),
\t * which the MIPS bootloader needs. */
\tpr_info("pvr-mtk: FW alloc '%s' align=%llu page_log2=%u\\n",
\t        pszText, (unsigned long long)uiAlign, (unsigned int)ExactLog2(uiAlign));
\teError = DevmemAllocateExportable(psDeviceNode,
\t\t\t\t\t\t\t\t\t  uiSize,
\t\t\t\t\t\t\t\t\t  uiAlign,
\t\t\t\t\t\t\t\t\t  ExactLog2(uiAlign),
\t\t\t\t\t\t\t\t\t  uiFlags,
\t\t\t\t\t\t\t\t\t  pszText,
\t\t\t\t\t\t\t\t\t  ppsMemDescPtr);"""
assert old in s, "pattern not found"
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("fw page size forced to align")
