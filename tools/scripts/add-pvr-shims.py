import os

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
D = os.path.join(R, "include/kernel_libc_compat")
os.makedirs(D, exist_ok=True)

files = {
"stdarg.h": """#ifndef __PVR_STDARG_H
#define __PVR_STDARG_H
#include <linux/stdarg.h>
#endif
""",
"stddef.h": """#ifndef __PVR_STDDEF_H
#define __PVR_STDDEF_H
#include <linux/stddef.h>
#include <linux/types.h>
#ifndef NULL
#define NULL ((void *)0)
#endif
#endif
""",
"stdbool.h": """#ifndef __PVR_STDBOOL_H
#define __PVR_STDBOOL_H
#include <linux/types.h>
#ifndef true
#define true 1
#endif
#ifndef false
#define false 0
#endif
#endif
""",
"stdint.h": """#ifndef __PVR_STDINT_H
#define __PVR_STDINT_H
#include <linux/types.h>
typedef __s8 int8_t;
typedef __u8 uint8_t;
typedef __s16 int16_t;
typedef __u16 uint16_t;
typedef __s32 int32_t;
typedef __u32 uint32_t;
typedef __s64 int64_t;
typedef __u64 uint64_t;
typedef __kernel_size_t size_t;
typedef long intptr_t;
typedef unsigned long uintptr_t;
#endif
""",
"string.h": """#ifndef __PVR_STRING_H
#define __PVR_STRING_H
#include <linux/string.h>
#endif
""",
"stdio.h": """#ifndef __PVR_STDIO_H
#define __PVR_STDIO_H
#include <linux/kernel.h>
#include <linux/printk.h>
#endif
""",
"stdlib.h": """#ifndef __PVR_STDLIB_H
#define __PVR_STDLIB_H
#include <linux/kernel.h>
#include <linux/slab.h>
#endif
""",
}
for n, c in files.items():
    open(os.path.join(D, n), "w").write(c)
print("shims:", sorted(os.listdir(D)))

# add include path and forced prologue to the DDK Makefile
mp = os.path.join(R, "Makefile")
s = open(mp).read()
if "kernel_libc_compat" not in s:
    s = s.replace('ccflags-y += -DCONFIG_MACH_MT6765',
                  'ccflags-y += -DCONFIG_MACH_MT6765\n'
                  'ccflags-y += -I$(RGX_TOP)/include/kernel_libc_compat', 1)
    open(mp, "w").write(s)
    print("Makefile: include path added")
