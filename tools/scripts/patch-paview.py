import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(p).read()

if "ui32PaView" in s:
    print("already patched")
    raise SystemExit(0)

anchor = "\tIMG_UINT32 ui32Sync = 0xDEADBEEF;\n"
if anchor not in s:
    raise SystemExit("anchor1 missing")

ins = anchor + '''
	IMG_UINT32 ui32PaView = 0xDEADBEEF;
	{
		struct page *psPg = NULL;
		unsigned long long ullPa = 0;
		void *pvMap = NULL;

		if (psDevInfo->psPowSyncPrim && psDevInfo->psPowSyncPrim->pui32LinAddr)
		{
			psPg = vmalloc_to_page((void *)psDevInfo->psPowSyncPrim->pui32LinAddr);
			if (psPg)
			{
				ullPa = page_to_phys(psPg) +
				        offset_in_page((void *)psDevInfo->psPowSyncPrim->pui32LinAddr);
			}
		}
		if (ullPa != 0)
		{
			pvMap = memremap(ullPa & ~0xFFFULL, 0x1000, MEMREMAP_WC);
			if (pvMap != NULL)
			{
				ui32PaView = readl((void __iomem *)((char *)pvMap + (ullPa & 0xFFF)));
				memunmap(pvMap);
			}
		}
	}
'''
s = s.replace(anchor, ins, 1)

old_fmt = ('\tpr_info("pvr-mtk: POW[%s] sync=%u rtn=%08x fwaddr=%08x cpuva=%px kccb=%u/%u slot=%u pow=%u hwr=%08x fwirq=%u faults=%u\\n",\n'
           '\t\ttag, ui32Sync,\n')
new_fmt = ('\tpr_info("pvr-mtk: POW[%s] sync=%u paview=%08x rtn=%08x fwaddr=%08x cpuva=%px kccb=%u/%u kcmds=%u slot=%u pow=%u hwr=%08x fwirq=%u faults=%u\\n",\n'
           '\t\ttag, ui32Sync, ui32PaView,\n')
if old_fmt not in s:
    raise SystemExit("format anchor missing")
s = s.replace(old_fmt, new_fmt, 1)

old_args = ('\t\tpsDevInfo->psKernelCCBCtl->ui32WriteOffset,\n'
            '\t\tpsDevInfo->psKernelCCBCtl->ui32ReadOffset,\n'
            '\t\tui32Slot,\n')
new_args = ('\t\tpsDevInfo->psKernelCCBCtl->ui32WriteOffset,\n'
            '\t\tpsDevInfo->psKernelCCBCtl->ui32ReadOffset,\n'
            '\t\tpsDevInfo->psRGXFWIfFwOsData->ui32KCCBCmdsExecuted,\n'
            '\t\tui32Slot,\n')
if old_args not in s:
    raise SystemExit("args anchor missing")
s = s.replace(old_args, new_args, 1)

open(p, "w").write(s)
print("pvr_pow_snap extended: paview + kcmds")
