import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/include/config_kernel_user_mt6765.h")
s = open(P).read()

old = "/* #define PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC (disabled: osmem must use dma_alloc_coherent/CMA lowmem) */"
new = "#define PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC"
if old in s:
    s = s.replace(old, new)
    print("re-enabled SUPPRESS_DMA_AC")
elif "#define PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC" in s:
    print("already enabled")
else:
    raise SystemExit("anchor not found")

open(P, "w").write(s)
