#!/usr/bin/env python3
"""kernel: pvr_dump_rgn=N dumps the TA-written region header buffer at each kick"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxta3d.c')
s = p.read_text()

old = '''static IMG_BOOL g_bKickTiming;
static IMG_UINT64 g_ui64KickT0;
'''
new = '''static IMG_BOOL g_bKickTiming;
static IMG_UINT64 g_ui64KickT0;

static int pvr_dump_rgn;
module_param(pvr_dump_rgn, int, 0644);
MODULE_PARM_DESC(pvr_dump_rgn, "Dump the next N region header buffers (bytes)");
'''
assert s.count(old) == 1, 'param anchor'
s = s.replace(old, new, 1)

anchor = '''	PRGXFWIF_UFO_ADDR		*pauiClientPRUpdateUFOAddress = NULL;'''
new_block = '''	if (unlikely(pvr_dump_rgn > 0 && bKickTA && psKMHWRTDataSet)) {
		RGXFWIF_HWRTDATA *psHWRTData = NULL;
		pvr_dump_rgn--;
		if (DevmemAcquireCpuVirtAddr(psKMHWRTDataSet->psHWRTDataFwMemDesc,
		                             (void **)&psHWRTData) == PVRSRV_OK) {
			IMG_DEV_VIRTADDR sRgnAddr;
			IMG_DEV_PHYADDR sRgnPhys;

			sRgnAddr.uiAddr = psHWRTData->sRgnHeaderDevVAddr.uiAddr;
			pr_info("pvr-rgn: hwrt=%llx rgn_va=%llx stride=%x rgn=%llu\\n",
			        (unsigned long long)psHWRTData->sHWRTDataCommonFwAddr.ui32Addr,
			        (unsigned long long)sRgnAddr.uiAddr,
			        psHWRTData->ui32MTileStride,
			        (unsigned long long)psHWRTData->uiRgnHeaderSize);
			if (sRgnAddr.uiAddr &&
			    RGXTranslateDevVAddr(psDevInfo, OSGetCurrentProcessID(), 12,
			                         sRgnAddr, &sRgnPhys) == PVRSRV_OK) {
				void *pvRgn = phys_to_virt((phys_addr_t)sRgnPhys.uiAddr);

				print_hex_dump(KERN_INFO, "pvr-rgn: ", DUMP_PREFIX_OFFSET,
				               16, 1, pvRgn, 160, false);
			}
			DevmemReleaseCpuVirtAddr(psKMHWRTDataSet->psHWRTDataFwMemDesc);
		}
	}

''' + anchor
assert s.count(anchor) == 1, 'kick body anchor'
s = s.replace(anchor, new_block, 1)

p.write_text(s)
print('region header dump added')
