R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

# 1. enable contiguous (CMA) firmware memory for MIPS cores
p = R + "/include/config_kernel_user_mt6765.h"
s = open(p).read()
if "SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY" not in s:
    # put it next to the ION define
    s = s.replace("/* #define SUPPORT_ION */",
                  "/* #define SUPPORT_ION */\n#define SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY")
    open(p, "w").write(s)
    print("config: SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY added")
else:
    print("config: already")

# 2. log the FW allocation geometry
p = R + "/services/server/devices/rogue/rgxinit.c"
s = open(p).read()
old = "\tPVRSRV_ERROR eError = PVRSRV_OK;\n\tIMG_DEVMEM_LOG2ALIGN_T uiLog2Align = OSGetPageShift();\n"
new = old + """\tpr_info("pvr-mtk: FW mem '%s' size=%llu align_log2=%u\\n",
\t        pszText, (unsigned long long)ui32Size, (unsigned int)uiLog2Align);
"""
if "FW mem '%s' size=" not in s:
    assert old in s
    s = s.replace(old, new, 1)
    open(p, "w").write(s)
    print("rgxinit: FW alloc log added")
else:
    print("rgxinit: already")
