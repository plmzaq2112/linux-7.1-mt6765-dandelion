import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/include/config_kernel_user_mt6765.h")
s = open(P).read()

old = "#define PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC\n"
new = "/* #define PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC (disabled: need uncached coherent pages for host<->FW comms) */\n"
if old in s:
    s = s.replace(old, new)
    open(P, "w").write(s)
    print("SUPPRESS_DMA_AC disabled (coherent)")
elif "/* #define PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC" in s:
    print("already disabled")
else:
    raise SystemExit("anchor not found")
