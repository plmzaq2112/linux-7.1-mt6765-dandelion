R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = R + "/services/server/devices/rogue/rgxstartstop.c"
s = open(p).read()

# --- after each RGXAcquire*RemapAddr, log the physical address ---
adds = [
    ("\tRGXAcquireBootRemapAddr(hPrivate, &sPhyAddr);\n",
     "\tRGXAcquireBootRemapAddr(hPrivate, &sPhyAddr);\n"
     "\tpr_info(\"pvr-mtk: MIPS bus=%u boot_remap_pa=0x%llx\\n\",\n"
     "\t        (unsigned int)RGXGetDevicePhysBusWidth(hPrivate),\n"
     "\t        (unsigned long long)sPhyAddr.uiAddr);\n"),
    ("\tRGXAcquireDataRemapAddr(hPrivate, &sPhyAddr);\n",
     "\tRGXAcquireDataRemapAddr(hPrivate, &sPhyAddr);\n"
     "\tpr_info(\"pvr-mtk: MIPS data_remap_pa=0x%llx\\n\",\n"
     "\t        (unsigned long long)sPhyAddr.uiAddr);\n"),
    ("\tRGXAcquireCodeRemapAddr(hPrivate, &sPhyAddr);\n",
     "\tRGXAcquireCodeRemapAddr(hPrivate, &sPhyAddr);\n"
     "\tpr_info(\"pvr-mtk: MIPS code_remap_pa=0x%llx\\n\",\n"
     "\t        (unsigned long long)sPhyAddr.uiAddr);\n"),
]

for old, new in adds:
    if new.split("\n")[1] in s:
        continue
    assert old in s, old
    s = s.replace(old, new, 1)

open(p, "w").write(s)
print("mips remap logs added")

# --- move the FW alloc log after the align adjustment ---
p = R + "/services/server/devices/rogue/rgxinit.c"
s = open(p).read()
bad = """\tpr_info("pvr-mtk: FW mem '%s' size=%llu align_log2=%u\\n",
\t        pszText, (unsigned long long)ui32Size, (unsigned int)uiLog2Align);
"""
assert bad in s
s = s.replace(bad, "", 1)
anchor = "#endif\n\n#if defined(SUPPORT_DEDICATED_FW_MEMORY)"
assert anchor in s
s = s.replace(anchor,
              "#endif\n\n\tpr_info(\"pvr-mtk: FW mem '%s' size=%llu align_log2=%u (MIPS=%d)\\n\",\n"
              "\t        pszText, (unsigned long long)ui32Size, (unsigned int)uiLog2Align,\n"
              "\t        (int)RGX_IS_FEATURE_SUPPORTED(psDeviceNode->pvDevice, MIPS));\n\n"
              "#if defined(SUPPORT_DEDICATED_FW_MEMORY)", 1)
open(p, "w").write(s)
print("fw alloc log moved after alignment")
