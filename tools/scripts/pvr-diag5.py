R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

# ---- 1. rgxpower.c: SP read-back of FW memory (is DDR reachable by the GPU?) ----
p = R + "/services/server/devices/rogue/rgxpower.c"
s = open(p).read()
anchor = "\t\t\t\teError = PVRSRV_ERROR_TIMEOUT;\n"
assert anchor in s
add = """\t\t\t\t{
\t\t\t\t\tvoid *pvCPUVA = NULL;
\t\t\t\t\tIMG_UINT32 ui32GPUVal = 0xDEADBEEF;
\t\t\t\t\tPVRSRV_ERROR eRd;

\t\t\t\t\teRd = DevmemAcquireCpuVirtAddr(psDevInfo->psRGXFWCodeMemDesc, &pvCPUVA);
\t\t\t\t\tif (eRd == PVRSRV_OK)
\t\t\t\t\t{
\t\t\t\t\t\teRd = RGXReadMETAAddr(psDevInfo,
\t\t\t\t\t\t                      (IMG_UINT32)psDevInfo->sFWCodeDevVAddrBase.uiAddr,
\t\t\t\t\t\t                      &ui32GPUVal);
\t\t\t\t\t\tpr_info("pvr-mtk: FW[0] cpu=%08x gpu=%08x rc=%d\\n",
\t\t\t\t\t\t        *(IMG_UINT32 *)pvCPUVA, ui32GPUVal, eRd);
\t\t\t\t\t\tDevmemReleaseCpuVirtAddr(psDevInfo->psRGXFWCodeMemDesc);
\t\t\t\t\t}
\t\t\t\t\telse
\t\t\t\t\t{
\t\t\t\t\t\tpr_info("pvr-mtk: FW code CPU VA unavailable (%d)\\n", eRd);
\t\t\t\t\t}

\t\t\t\t\tpr_info("pvr-mtk: mslvctrl1=%08x mslvirqstatus=%08x\\n",
\t\t\t\t\t        OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_META_SP_MSLVCTRL1),
\t\t\t\t\t        OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_META_SP_MSLVIRQSTATUS));
\t\t\t\t}
""" + anchor
if "FW[0] cpu=" not in s:
    s = s.replace(anchor, add, 1)
    open(p, "w").write(s)
    print("rgxpower: SP readback added")
else:
    print("rgxpower: already there")

# ---- 2. platform: re-apply vendor power-on sequence at PostPowerState ----
p = R + "/services/system/rogue/rgx_mtk/pvr_platform_mt6765.c"
s = open(p).read()
old = """PVRSRV_ERROR MTKDevPostPowerState(IMG_HANDLE hSysData,
\t\t\t\t  PVRSRV_DEV_POWER_STATE eNewPowerState,
\t\t\t\t  PVRSRV_DEV_POWER_STATE eCurrentPowerState,
\t\t\t\t  IMG_BOOL bForced)
{
\treturn PVRSRV_OK;
}"""
new = """PVRSRV_ERROR MTKDevPostPowerState(IMG_HANDLE hSysData,
\t\t\t\t  PVRSRV_DEV_POWER_STATE eNewPowerState,
\t\t\t\t  PVRSRV_DEV_POWER_STATE eCurrentPowerState,
\t\t\t\t  IMG_BOOL bForced)
{
\tif (eCurrentPowerState == PVRSRV_DEV_POWER_STATE_OFF &&
\t    eNewPowerState == PVRSRV_DEV_POWER_STATE_ON) {
\t\t/* vendor order: clock -> CG -> APM, right before RGXStart */
\t\tclk_prepare_enable(mfg_clk);
\t\tif (mfgcfg_rm) {
\t\t\tregmap_write(mfgcfg_rm, 0x8, 0xf);
\t\t\tpvr_mtk_init_apm();
\t\t}
\t\tpr_info("pvr-mtk: PostPowerState ON (clk+CG+APM reapplied)\\n");
\t}
\treturn PVRSRV_OK;
}"""
if "PostPowerState ON (clk+CG+APM" not in s:
    assert old in s
    s = s.replace(old, new, 1)
    open(p, "w").write(s)
    print("platform: PostPowerState implemented")
else:
    print("platform: already there")
