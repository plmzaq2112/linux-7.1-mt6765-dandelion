R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = R + "/include/config_kernel_user_mt6765.h"
s = open(p).read()

changed = False
for name in ("PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC",
             "PVR_LINUX_PHYSMEM_USE_HIGHMEM_ONLY"):
    line = "#define %s\n" % name
    if line in s:
        s = s.replace(line, "/* %s (disabled: osmem must use dma_alloc_coherent/CMA lowmem) */\n" % line.strip(), 1)
        changed = True
        print("disabled", name)
    else:
        print("not found:", name)

if changed:
    open(p, "w").write(s)
