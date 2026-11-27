R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = R + "/services/server/devices/rogue/rgxinit.c"
s = open(p).read()
anchor = "\tif (RGX_IS_FEATURE_VALUE_SUPPORTED(psDevInfo, META) ||\n\t    RGX_IS_FEATURE_SUPPORTED(psDevInfo, RISCV_FW_PROCESSOR))\n"
add = """\tpr_info("pvr-mtk: BVNC=%u.%u.%u.%u META_val=%d META_sup=%d MIPS_sup=%d RISCV_sup=%d\\n",
\t        psDevInfo->sDevFeatureCfg.ui32B, psDevInfo->sDevFeatureCfg.ui32V,
\t        psDevInfo->sDevFeatureCfg.ui32N, psDevInfo->sDevFeatureCfg.ui32C,
\t        (int)RGX_GET_FEATURE_VALUE(psDevInfo, META),
\t        (int)RGX_IS_FEATURE_VALUE_SUPPORTED(psDevInfo, META),
\t        (int)RGX_IS_FEATURE_SUPPORTED(psDevInfo, MIPS),
\t        (int)RGX_IS_FEATURE_SUPPORTED(psDevInfo, RISCV_FW_PROCESSOR));
""" + anchor
if "META_val=" not in s:
    assert anchor in s
    s = s.replace(anchor, add, 1)
    open(p, "w").write(s)
    print("feature print added")
else:
    print("already")
