p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/Makefile"
s = open(p).read()

# remove misplaced line (before RGX_TOP is defined)
s = s.replace("ccflags-y += -DCONFIG_MACH_MT6765\nccflags-y += -I$(RGX_TOP)/include/kernel_libc_compat",
              "ccflags-y += -DCONFIG_MACH_MT6765")

# add after RGX_TOP definition / -include line
needle = 'ccflags-y += -include $(RGX_TOP)/include/config_kernel_user_$(MTK_PLATFORM)$(ECO).h\n'
if "kernel_libc_compat" not in s:
    s = s.replace(needle, needle + 'ccflags-y += -I$(RGX_TOP)/include/kernel_libc_compat\n', 1)

open(p, "w").write(s)
print(open(p).read()[:600])
