import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(p).read()

start = s.find("static void pvr_dump_fw_trace(")
end = s.find("static void pvr_maybe_move_prim(PVRSRV_RGXDEV_INFO *psDevInfo);", start)
if start < 0 or end < 0:
    raise SystemExit("markers not found")

new = r'''static void pvr_dump_fw_trace(PVRSRV_RGXDEV_INFO *psDevInfo, const char *pcTag)
{
	RGXFWIF_TRACEBUF *psTb = psDevInfo->psRGXFWIfTraceBufCtl;
	IMG_UINT32 ui32Size;
	IMG_UINT32 tid;

	if (psTb == NULL)
	{
		pr_info("pvr-mtk: FWT %s: no control buffer\n", pcTag);
		return;
	}

	ui32Size = psTb->ui32TraceBufSizeInDWords;
	pr_info("pvr-mtk: FWT %s logtype=%08x size=%u flags=%08x threads=%u ctl_fw=%08x\n",
	        pcTag, psTb->ui32LogType, ui32Size, psTb->ui32TracebufFlags,
	        (unsigned)RGXFW_THREAD_NUM,
	        (psDevInfo->psRGXFWIfSysInit != NULL) ?
	            psDevInfo->psRGXFWIfSysInit->sTraceBufCtl.ui32Addr : 0U);

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

	for (tid = 0; tid < RGXFW_THREAD_NUM; tid++)
	{
		void *pvCpu = NULL;
		IMG_UINT32 i, ui32Start, ui32Count;
		IMG_UINT32 ui32Ptr = psTb->sTraceBuf[tid].ui32TracePointer;

		pr_info("pvr-mtk: FWT %s tid=%u ptr=%u buf_fw=%08x field=%016lx\n",
		        pcTag, tid, ui32Ptr,
		        psTb->sTraceBuf[tid].pui32RGXFWIfTraceBuffer.ui32Addr,
		        (unsigned long)psTb->sTraceBuf[tid].pui32TraceBuffer);

		if (psDevInfo->psRGXFWIfTraceBufferMemDesc[tid] == NULL)
		{
			pr_info("pvr-mtk: FWT %s tid=%u: no memdesc\n", pcTag, tid);
			continue;
		}
		if (DevmemAcquireCpuVirtAddr(psDevInfo->psRGXFWIfTraceBufferMemDesc[tid], &pvCpu) != PVRSRV_OK ||
		    pvCpu == NULL)
		{
			pr_info("pvr-mtk: FWT %s tid=%u: acquire cpu va failed\n", pcTag, tid);
			continue;
		}
		pr_info("pvr-mtk: FWT %s tid=%u fresh cpu=%px\n", pcTag, tid, pvCpu);

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
				pr_info("FWTRAW t%u %u: %08x %08x %08x %08x %08x %08x %08x %08x\n",
				        tid, ui32Start + i,
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
		DevmemReleaseCpuVirtAddr(psDevInfo->psRGXFWIfTraceBufferMemDesc[tid]);
	}
}

'''
s = s[:start] + new + s[end:]
open(p, "w").write(s)
print("two-thread dump written")
