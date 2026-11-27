R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

# ---- A. rgxinit.c : print the MMU page-catalogue physical address ----
p = R + "/services/server/devices/rogue/rgxinit.c"
s = open(p).read()
old = "\t\tpsDevInfo->sLayerParams.sPCAddr = sKernelMMUCtxPCAddr;\n"
new = old + """\t\tpr_info("pvr-mtk: MMU page catalogue phys = 0x%llx\\n",
\t\t        (unsigned long long)sKernelMMUCtxPCAddr.uiAddr);
"""
if "MMU page catalogue phys" not in s:
    assert old in s
    s = s.replace(old, new, 1)
    open(p, "w").write(s)
    print("rgxinit: MMU PC print added")
else:
    print("rgxinit: already")

# ---- B. rgxpower.c : dump BIF/MMU/Garten state when the FW fails to start ----
p = R + "/services/server/devices/rogue/rgxpower.c"
s = open(p).read()
anchor = """\t\t\t\t\tpr_info("pvr-mtk: mslvctrl1=%08x mslvirqstatus=%08x\\n",
\t\t\t\t\t        OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_META_SP_MSLVCTRL1),
\t\t\t\t\t        OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_META_SP_MSLVIRQSTATUS));
"""
add = anchor + """\t\t\t\t\tpr_info("pvr-mtk: bif_cat0=%llx mmu_fault=%llx mmu_cbase=%llx garten=%llx\\n",
\t\t\t\t\t        (unsigned long long)OSReadHWReg64(psDevInfo->pvRegsBaseKM, RGX_CR_BIF_CAT_BASE0),
\t\t\t\t\t        (unsigned long long)OSReadHWReg64(psDevInfo->pvRegsBaseKM, RGX_CR_MMU_FAULT_STATUS),
\t\t\t\t\t        (unsigned long long)OSReadHWReg64(psDevInfo->pvRegsBaseKM, RGX_CR_MMU_CBASE_MAPPING),
\t\t\t\t\t        (unsigned long long)OSReadHWReg64(psDevInfo->pvRegsBaseKM, RGX_CR_MTS_GARTEN_WRAPPER_CONFIG));
"""
if "bif_cat0=" not in s:
    assert anchor in s
    s = s.replace(anchor, add, 1)
    open(p, "w").write(s)
    print("rgxpower: BIF/MMU dump added")
else:
    print("rgxpower: already")
