import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(p).read()

if "FWT alloc=" in s:
    print("already patched")
    raise SystemExit(0)

old = '''		if (psDevInfo->psRGXFWIfTraceBufCtl != NULL)
		{
			RGXFWIF_TRACEBUF *psTb = psDevInfo->psRGXFWIfTraceBufCtl;
			pr_info("pvr-mtk: FWT boot logtype=%08x\\n", psTb->ui32LogType);
			psTb->ui32LogType |= (RGXFWIF_LOG_TYPE_TRACE |
			                      RGXFWIF_LOG_TYPE_GROUP_MAIN |
			                      RGXFWIF_LOG_TYPE_GROUP_POW);
			pr_info("pvr-mtk: FWT boot logtype now=%08x\\n", psTb->ui32LogType);
		}
'''
new = '''		if (psDevInfo->psRGXFWIfTraceBufCtl != NULL)
		{
			RGXFWIF_TRACEBUF *psTb = psDevInfo->psRGXFWIfTraceBufCtl;

			pr_info("pvr-mtk: FWT boot logtype=%08x size=%u\\n",
			        psTb->ui32LogType, psTb->ui32TraceBufSizeInDWords);
			if (psTb->ui32TraceBufSizeInDWords == 0)
			{
				PVRSRV_ERROR eTb = RGXTraceBufferInitOnDemandResources(psDevInfo,
				                                                       RGX_FWSHAREDMEM_CPU_RO_ALLOCFLAGS);
				pr_info("pvr-mtk: FWT alloc=%d size=%u fwaddr=%08x buf=%p\\n",
				        eTb, psTb->ui32TraceBufSizeInDWords,
				        psTb->sTraceBuf[0].pui32RGXFWIfTraceBuffer.ui32Addr,
				        (void *)psTb->sTraceBuf[0].pui32TraceBuffer);
			}
			psTb->ui32LogType = (RGXFWIF_LOG_TYPE_TRACE |
			                     RGXFWIF_LOG_TYPE_GROUP_MAIN |
			                     RGXFWIF_LOG_TYPE_GROUP_POW);
			pr_info("pvr-mtk: FWT logtype now=%08x\\n", psTb->ui32LogType);
		}
'''
if old not in s:
    raise SystemExit("anchor missing")
s = s.replace(old, new, 1)

# ensure rgxmem.h is included for the alloc flags macro
if '#include "rgxmem.h"' not in s:
    s = s.replace('#include "rgxpower.h"\n', '#include "rgxpower.h"\n#include "rgxmem.h"\n', 1)

open(p, "w").write(s)
print("trace alloc hooked")
