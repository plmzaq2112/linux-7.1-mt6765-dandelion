#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk")

# rgxmem.c: insert after RGXCheckFaultAddress
p = ROOT / "services/server/devices/rogue/rgxmem.c"
s = p.read_text(encoding="utf-8")
if "RGXTranslateDevVAddr" not in s:
    old = """out_unlock:
	OSWRLockReleaseRead(psDevInfo->hMemoryCtxListLock);
}

"""
    new = """out_unlock:
	OSWRLockReleaseRead(psDevInfo->hMemoryCtxListLock);
}

PVRSRV_ERROR RGXTranslateDevVAddr(PVRSRV_RGXDEV_INFO *psDevInfo,
                                  IMG_PID uiPID,
                                  IMG_UINT32 uiLog2PageSize,
                                  IMG_DEV_VIRTADDR sDevVAddr,
                                  IMG_DEV_PHYADDR *psPhysAddr)
{
	DLLIST_NODE *psNode, *psNext;
	PVRSRV_ERROR eError = PVRSRV_ERROR_NOT_FOUND;

	OSWRLockAcquireRead(psDevInfo->hMemoryCtxListLock);

	dllist_foreach_node(&psDevInfo->sMemoryContextList, psNode, psNext)
	{
		SERVER_MMU_CONTEXT *psServerMMUContext =
			IMG_CONTAINER_OF(psNode, SERVER_MMU_CONTEXT, sNode);

		if (psServerMMUContext->uiPID == uiPID)
		{
			eError = MMU_GetVDevAddrPhys(psServerMMUContext->psMMUContext,
			                             uiLog2PageSize,
			                             sDevVAddr,
			                             psPhysAddr);
			break;
		}
	}

	OSWRLockReleaseRead(psDevInfo->hMemoryCtxListLock);

	return eError;
}

"""
    assert s.count(old) == 1
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print("patched rgxmem.c")
else:
    print("rgxmem.c already patched")

# rgxta3d.c: module param + dump
p = ROOT / "services/server/devices/rogue/rgxta3d.c"
s = p.read_text(encoding="utf-8")
if "pvr_dump_stream" in s:
    print("rgxta3d.c already patched")
    raise SystemExit(0)

if "#include <linux/io.h>" not in s:
    anchor = "#include <linux/stddef.h>\n"
    assert s.count(anchor) == 1
    s = s.replace(anchor, anchor + "#include <linux/io.h>\n", 1)

old = """static int pvr_dump_kick;
module_param(pvr_dump_kick, int, 0644);
MODULE_PARM_DESC(pvr_dump_kick, "Dump next N KickTA3D CMDTA/CMD3D structs to dmesg");
"""
new = old + """
static int pvr_dump_stream;
module_param(pvr_dump_stream, int, 0644);
MODULE_PARM_DESC(pvr_dump_stream, "Dump next N 1.13 VDM control streams via MMU translation");
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

old = """		if (bKick3D && pui83DDMCmd && ui323DCmdSize)
			print_hex_dump(KERN_INFO, "pvr-dump-3D: ", DUMP_PREFIX_OFFSET, 16, 4,
				       pui83DDMCmd, ui323DCmdSize, false);
	}
"""
new = """		if (bKick3D && pui83DDMCmd && ui323DCmdSize)
			print_hex_dump(KERN_INFO, "pvr-dump-3D: ", DUMP_PREFIX_OFFSET, 16, 4,
				       pui83DDMCmd, ui323DCmdSize, false);
	}

	if (unlikely(pvr_dump_stream > 0 && bKickTA && pui8TADMCmd &&
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
	}
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("patched rgxta3d.c")
