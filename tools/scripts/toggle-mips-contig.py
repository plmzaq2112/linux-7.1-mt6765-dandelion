import os, re
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/include/config_kernel_user_mt6765.h")
s = open(P).read()
if "// #define SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY" in s:
    print("already disabled")
else:
    s = s.replace("#define SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY",
                  "// #define SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY")
    open(P, "w").write(s)
    print("disabled SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY")
