import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(p).read()

start = s.find("static void pvr_fwtrace_printf(")
end = s.find("static void pvr_maybe_move_prim(PVRSRV_RGXDEV_INFO *psDevInfo);", start)
if start < 0 or end < 0:
    raise SystemExit("markers not found")

new = r'''static void pvr_dump_fw_trace(PVRSRV_RGXDEV_INFO *psDevInfo, const char *pcTag)
{
	RGXFWIF_TRACEBUF *psTb = psDevInfo->psRGXFWIfTraceBufCtl;
	IMG_UINT32 ui32Size, ui32Ptr;

	if (psTb == NULL)
	{
		pr_info("pvr-mtk: FWT %s: no control buffer\n", pcTag);
		return;
	}
	ui32Size = psTb->ui32TraceBufSizeInDWords;
	ui32Ptr  = psTb->sTraceBuf[0].ui32TracePointer;
	pr_info("pvr-mtk: FWT %s logtype=%08x size=%u ptr=%u field=%016lx\n",
	        pcTag, psTb->ui32LogType, ui32Size, ui32Ptr,
	        (unsigned long)psTb->sTraceBuf[0].pui32TraceBuffer);

	if ((psTb->ui32LogType & RGXFWIF_LOG_TYPE_GROUP_MASK) == 0)
	{
		pr_info("pvr-mtk: FWT %s: logging disabled\n", pcTag);
		return;
	}
	if (ui32Size == 0)
	{
		pr_info("pvr-mtk: FWT %s: size 0\n", pcTag);
		return;
	}
	if (psDevInfo->psRGXFWIfTraceBufferMemDesc[0] == NULL)
	{
		pr_info("pvr-mtk: FWT %s: no memdesc\n", pcTag);
		return;
	}

	{
		void *pvCpu = NULL;
		IMG_UINT32 i, ui32Start, ui32Count;

		if (DevmemAcquireCpuVirtAddr(psDevInfo->psRGXFWIfTraceBufferMemDesc[0], &pvCpu) != PVRSRV_OK ||
		    pvCpu == NULL)
		{
			pr_info("pvr-mtk: FWT %s: acquire cpu va failed\n", pcTag);
			return;
		}
		pr_info("pvr-mtk: FWT %s: fresh cpu=%px\n", pcTag, pvCpu);

		if (((unsigned long)pvCpu >> 48) == 0xffffUL)
		{
			IMG_UINT32 *pui32 = (IMG_UINT32 *)pvCpu;

			ui32Count = 160;
			if (ui32Count > ui32Size)
			{
				ui32Count = ui32Size;
			}
			ui32Start = (ui32Ptr + ui32Size - ui32Count) % ui32Size;

			for (i = 0; i < ui32Count; i += 8)
			{
				pr_info("FWTRAW %u: %08x %08x %08x %08x %08x %08x %08x %08x\n",
				        ui32Start + i,
				        pui32[(ui32Start + i + 0) % ui32Size],
				        pui32[(ui32Start + i + 1) % ui32Size],
				        pui32[(ui32Start + i + 2) % ui32Size],
				        pui32[(ui32Start + i + 3) % ui32Size],
				        pui32[(ui32Start + i + 4) % ui32Size],
				        pui32[(ui32Start + i + 5) % ui32Size],
				        pui32[(ui32Start + i + 6) % ui32Size],
				        pui32[(ui32Start + i + 7) % ui32Size]);
			}
		}
		DevmemReleaseCpuVirtAddr(psDevInfo->psRGXFWIfTraceBufferMemDesc[0]);
	}
}

'''
s = s[:start] + new + s[end:]

# drop the now-unused extern for the trace limit
s = s.replace("extern IMG_UINT32 g_pvrFwTraceLimit;\n", "")

open(p, "w").write(s)
print("dump rewritten")
