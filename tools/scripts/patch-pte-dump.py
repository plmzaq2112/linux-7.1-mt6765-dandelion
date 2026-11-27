import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "PTE[%03x]" in s:
    print("already patched")
    raise SystemExit(0)

# includes
a = '#include "rgxdefs_km.h"\n'
i = s.find(a)
if i < 0:
    raise SystemExit("include anchor not found")
s = s[:i + len(a)] + '#include <linux/io.h>\n#include "mmu_common.h"\n' + s[i + len(a):]

anchor = '\t\tpr_info("pvr-mtk: RT cfg=%08x pm=%u clk=%u dusts=%u syscfg=%08x syscfgx=%08x\\n",\n'
j = s.find(anchor)
if j < 0:
    raise SystemExit("RT cfg anchor not found")

ins = r'''		{
			IMG_DEV_PHYADDR sPtAddr;
			if (MMU_AcquireBaseAddr(psDevInfo->psKernelMMUCtx, &sPtAddr) == PVRSRV_OK)
			{
				void *pvPt = memremap(sPtAddr.uiAddr, 0x10000, MEMREMAP_WB);
				pr_info("pvr-mtk: PT base pa=0x%llx map=%p\n",
				        (unsigned long long)sPtAddr.uiAddr, pvPt);
				if (pvPt)
				{
					unsigned int k;
					unsigned int *pui32 = (unsigned int *)pvPt;
					for (k = 0x10; k < 0x30; k++)
					{
						unsigned int e = pui32[k];
						pr_info("pvr-mtk: PTE[%03x] va=%08x raw=%08x v=%u pa=0x%llx cache=%u\n",
						        k, 0xC0000000u + (k << 12), e, (e >> 1) & 1u,
						        (unsigned long long)(((unsigned long long)(e & 0x03FFFFC0u)) << 6),
						        (e >> 3) & 7u);
					}
					memunmap(pvPt);
				}
			}
			else
			{
				pr_info("pvr-mtk: MMU_AcquireBaseAddr failed\n");
			}
		}
'''
s = s[:j] + ins + s[j:]
open(P, "w").write(s)
print("PTE dump added")
