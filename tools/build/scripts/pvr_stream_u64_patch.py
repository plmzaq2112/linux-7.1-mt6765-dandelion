#!/usr/bin/env python3
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxta3d.c")
s = P.read_text(encoding="utf-8")

old = """	if (unlikely(pvr_dump_stream > 0 && bKickTA && pui8TADMCmd &&
	             ui32TACmdSize >= 0x18)) {
		IMG_UINT32 ui32VdmAddr = *(IMG_UINT32 *)(pui8TADMCmd + 0x10);
		IMG_UINT32 ui32VdmSize = *(IMG_UINT32 *)(pui8TADMCmd + 0x14);
		IMG_DEV_VIRTADDR sDevVAddr = { .uiAddr = ui32VdmAddr };
		IMG_DEV_PHYADDR sPhysAddr;
		PVRSRV_ERROR eError;

		eError = RGXTranslateDevVAddr(psDevInfo,
		                              OSGetCurrentProcessID(),
		                              12,
		                              sDevVAddr,
		                              &sPhysAddr);
		if (eError == PVRSRV_OK) {
			void *pvCpu = phys_to_virt((phys_addr_t)sPhysAddr.uiAddr);

			pvr_dump_stream--;
			pr_info("pvr-stream: va=%08x size=%u phys=%llx\\n",
			        ui32VdmAddr, ui32VdmSize,
			        (unsigned long long)sPhysAddr.uiAddr);
			print_hex_dump(KERN_INFO, "pvr-stream: ", DUMP_PREFIX_OFFSET,
			               16, 4, pvCpu,
			               ui32VdmSize > 256 ? 256 : ui32VdmSize, false);
		} else {
			pvr_dump_stream--;
			pr_info("pvr-stream: va=%08x translate err=%d\\n",
			        ui32VdmAddr, eError);
		}
	}"""

new = """	if (unlikely(pvr_dump_stream > 0 && bKickTA && pui8TADMCmd &&
	             ui32TACmdSize >= 0x18)) {
		IMG_UINT64 ui64VdmAddr = *(IMG_UINT64 *)(pui8TADMCmd + 0x10);
		IMG_DEV_VIRTADDR sDevVAddr = { .uiAddr = ui64VdmAddr };
		IMG_DEV_PHYADDR sPhysAddr;
		PVRSRV_ERROR eError;

		eError = RGXTranslateDevVAddr(psDevInfo,
		                              OSGetCurrentProcessID(),
		                              12,
		                              sDevVAddr,
		                              &sPhysAddr);
		if (eError == PVRSRV_OK) {
			void *pvCpu = phys_to_virt((phys_addr_t)sPhysAddr.uiAddr);

			pvr_dump_stream--;
			pr_info("pvr-stream: va=%llx phys=%llx\\n",
			        (unsigned long long)ui64VdmAddr,
			        (unsigned long long)sPhysAddr.uiAddr);
			print_hex_dump(KERN_INFO, "pvr-stream: ", DUMP_PREFIX_OFFSET,
			               16, 4, pvCpu, 256, false);
		} else {
			pvr_dump_stream--;
			pr_info("pvr-stream: va=%llx translate err=%d\\n",
			        (unsigned long long)ui64VdmAddr, eError);
		}
	}"""

assert s.count(old) == 1
P.write_text(s.replace(old, new, 1), encoding="utf-8")
print("patched full u64 stream va")
