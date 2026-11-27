import os, re

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

pro = os.path.join(R, "include/pvr_compat_prologue.h")
open(pro, "w").write("""#ifndef __PVR_COMPAT_PROLOGUE_H
#define __PVR_COMPAT_PROLOGUE_H
#include <linux/string.h>
/* strlcpy was removed from the kernel; strscpy has the same call signature */
#define strlcpy(dst, src, n) strscpy(dst, src, n)
#endif
""")
print("prologue written")

mp = os.path.join(R, "Makefile")
s = open(mp).read()
if "pvr_compat_prologue" not in s:
    s = s.replace("ccflags-y += -I$(RGX_TOP)/include/kernel_libc_compat",
                  "ccflags-y += -I$(RGX_TOP)/include/kernel_libc_compat\n"
                  "ccflags-y += -include $(RGX_TOP)/include/pvr_compat_prologue.h", 1)
    open(mp, "w").write(s)
print("Makefile prologue added")

# vm_map_ram: 7.1 dropped the prot argument
files = [
    "services/system/rogue/common/env/linux/dma_support.c",
    "services/server/env/linux/physmem_osmem_linux.c",
]
for f in files:
    p = os.path.join(R, f)
    t = open(p).read()
    n1 = t.count(", -1, prot)")
    n2 = t.count(", -1, pgprot)")
    t = t.replace(", -1, prot)", ", -1)").replace(", -1, pgprot)", ", -1)")
    open(p, "w").write(t)
    print(f, "patched", n1, n2)
