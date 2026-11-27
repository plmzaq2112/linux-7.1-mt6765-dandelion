import re, sys

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

# --- 1. rgxpower.c: dump boot-stage / META state when the FW fails to start ---
p = R + "/services/server/devices/rogue/rgxpower.c"
s = open(p).read()
marker = "\t\t\t\tPVR_DPF((PVR_DBG_ERROR, \"RGXPostPowerState: Polling for 'FW started' flag failed.\"));"
if "pvr-mtk: boot stage" not in s:
    add = marker + """
\t\t\t\tPVR_LOG(("pvr-mtk: boot stage=%u meta_boot=%08x soft_reset=%08x sys_bus_secure=%08x slc_idle=%08x sidekick_idle=%08x",
\t\t\t\t         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_FW_BOOT_STAGE_REGISTER),
\t\t\t\t         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_META_BOOT),
\t\t\t\t         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_SOFT_RESET),
\t\t\t\t         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_SYS_BUS_SECURE),
\t\t\t\t         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_SLC_IDLE),
\t\t\t\t         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_SIDEKICK_IDLE)));"""
    assert marker in s
    s = s.replace(marker, add, 1)
    open(p, "w").write(s)
    print("rgxpower.c patched")
else:
    print("rgxpower.c already patched")

# --- 2. rgxinit.c: print the FW heap device VA + sizes ---
p = R + "/services/server/devices/rogue/rgxinit.c"
s = open(p).read()
old = """\teError = DevmemAcquireDevVirtAddr(psDevInfo->psRGXFWCodeMemDesc,
\t\t\t&psDevInfo->sFWCodeDevVAddrBase);"""
new = old + """
\tPVR_LOG(("pvr-mtk: fw code DevVAddr=%"IMG_UINT64_FMTSPECx" (want %"IMG_UINT64_FMTSPECx"), data DevVAddr pending",
\t         psDevInfo->sFWCodeDevVAddrBase.uiAddr,
\t         (IMG_UINT64)RGX_FIRMWARE_RAW_HEAP_BASE));"""
if "pvr-mtk: fw code DevVAddr" not in s:
    assert old in s
    s = s.replace(old, new, 1)
    open(p, "w").write(s)
    print("rgxinit.c patched")
else:
    print("rgxinit.c already patched")
