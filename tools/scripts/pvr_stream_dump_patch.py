#!/usr/bin/env python3
"""Add a debug path to translate the 1.13 TA vdm_ctrl_stream_base to a physical
address and dump the 128-byte control stream from the kernel."""
from pathlib import Path

ROOT = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk")

# 1) mmu_common.h: declare MMU_GetVDevAddrPhys
p = ROOT / "services/server/include/mmu_common.h"
s = p.read_text(encoding="utf-8")
if "MMU_GetVDevAddrPhys" not in s:
    old = """IMG_BOOL MMU_IsVDevAddrValid(MMU_CONTEXT *psMMUContext,
                             IMG_UINT32 uiLog2PageSize,
                             IMG_DEV_VIRTADDR sDevVAddr);
"""
    new = old + """
PVRSRV_ERROR MMU_GetVDevAddrPhys(MMU_CONTEXT *psMMUContext,
                                 IMG_UINT32 uiLog2PageSize,
                                 IMG_DEV_VIRTADDR sDevVAddr,
                                 IMG_DEV_PHYADDR *psPhysAddr);
"""
    assert s.count(old) == 1
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print("patched mmu_common.h")

# 2) mmu_common.c: implement MMU_GetVDevAddrPhys
p = ROOT / "services/server/common/mmu_common.c"
s = p.read_text(encoding="utf-8")
if "MMU_GetVDevAddrPhys" not in s:
    old = """	_MMU_PutPTConfig(psMMUContext, hPriv);

	return bStatus;
}

#if defined(PDUMP)
"""
    new = """	_MMU_PutPTConfig(psMMUContext, hPriv);

	return bStatus;
}

PVRSRV_ERROR MMU_GetVDevAddrPhys(MMU_CONTEXT *psMMUContext,
                                 IMG_UINT32 uiLog2PageSize,
                                 IMG_DEV_VIRTADDR sDevVAddr,
                                 IMG_DEV_PHYADDR *psPhysAddr)
{
	const MMU_PxE_CONFIG *psConfig;
	const MMU_DEVVADDR_CONFIG *psDevVAddrConfig;
	IMG_HANDLE hPriv;
	IMG_BOOL bStatus = IMG_FALSE;
	IMG_UINT64 ui64Entry;
	IMG_UINT64 ui64Page;

	_MMU_GetPTConfig(psMMUContext, uiLog2PageSize, &psConfig, &hPriv, &psDevVAddrConfig);

	ui64Entry = MMU_GetVDevAddrPTE(psMMUContext,
	                               psConfig,
	                               psDevVAddrConfig,
	                               uiLog2PageSize,
	                               sDevVAddr,
	                               &bStatus);

	_MMU_PutPTConfig(psMMUContext, hPriv);

	if (!bStatus)
		return PVRSRV_ERROR_INVALID_PARAMS;

	ui64Page = (ui64Entry & psConfig->uiAddrMask) >> psConfig->uiAddrShift;
	psPhysAddr->uiAddr = (ui64Page << psConfig->uiAddrShift) |
	                     (sDevVAddr.uiAddr & ((1ULL << uiLog2PageSize) - 1));

	return PVRSRV_OK;
}

#if defined(PDUMP)
"""
    assert s.count(old) == 1
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print("patched mmu_common.c")

# 3) rgxmem.h: declare RGXTranslateDevVAddr
p = ROOT / "services/server/devices/rogue/rgxmem.h"
s = p.read_text(encoding="utf-8")
if "RGXTranslateDevVAddr" not in s:
    old = """void RGXCheckFaultAddress(PVRSRV_RGXDEV_INFO *psDevInfo,
				IMG_DEV_VIRTADDR *psDevVAddr,
				IMG_DEV_PHYADDR *psDevPAddr,
				MMU_FAULT_DATA *psOutFaultData);
"""
    new = old + """
PVRSRV_ERROR RGXTranslateDevVAddr(PVRSRV_RGXDEV_INFO *psDevInfo,
                                  IMG_PID uiPID,
                                  IMG_UINT32 uiLog2PageSize,
                                  IMG_DEV_VIRTADDR sDevVAddr,
                                  IMG_DEV_PHYADDR *psPhysAddr);
"""
    assert s.count(old) == 1
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print("patched rgxmem.h")

# 4) rgxmem.c: implement RGXTranslateDevVAddr
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

# 5) rgxta3d.c: module param + dump
p = ROOT / "services/server/devices/rogue/rgxta3d.c"
s = p.read_text(encoding="utf-8")
if "pvr_dump_stream" not in s:
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

print("done")
