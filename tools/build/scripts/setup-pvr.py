import os, re, sys

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline"
A = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/artifacts"

# 1. pvr Kconfig/Makefile
os.makedirs(os.path.join(R, "drivers/misc/pvr"), exist_ok=True)
open(os.path.join(R, "drivers/misc/pvr/Kconfig"), "w").write(open(os.path.join(A, "pvr-Kconfig")).read())
open(os.path.join(R, "drivers/misc/pvr/Makefile"), "w").write(open(os.path.join(A, "pvr-Makefile")).read())

# 2. hook into drivers/misc
mk = os.path.join(R, "drivers/misc/Makefile")
s = open(mk).read()
if "pvr/" not in s:
    s += "\nobj-$(CONFIG_DRM_PVR_LEGACY)\t+= pvr/\n"
    open(mk, "w").write(s)
    print("drivers/misc/Makefile updated")

kc = os.path.join(R, "drivers/misc/Kconfig")
s = open(kc).read()
if "drivers/misc/pvr/Kconfig" not in s:
    if "endmenu" in s:
        s = s.replace("\nendmenu", "\nsource \"drivers/misc/pvr/Kconfig\"\nendmenu", 1)
    else:
        s += "\nsource \"drivers/misc/pvr/Kconfig\"\n"
    open(kc, "w").write(s)
    print("drivers/misc/Kconfig updated")

# 3. ddk Makefile tweaks
mp = os.path.join(R, "drivers/misc/pvr/ddk/Makefile")
s = open(mp).read()

# MTK_PLATFORM before the -include line
if "MTK_PLATFORM :=" not in s:
    s = s.replace('OPTIM = -Os', 'MTK_PLATFORM := mt6765\n\nOPTIM = -Os', 1)

# strip the 4.19 mt-plat include block
lines = s.split("\n")
out = []
skip = False
for ln in lines:
    if ln.strip().startswith("# GPU mt-plat:"):
        skip = True
        continue
    if skip:
        if ln.startswith("obj-"):
            skip = False
        else:
            continue
    out.append(ln)
s = "\n".join(out)

# obj line
s = s.replace("obj-$(CONFIG_MTK_GPU_SUPPORT) += pvrsrvkm.o",
              "obj-$(CONFIG_DRM_PVR_LEGACY) += pvrsrvkm.o")
open(mp, "w").write(s)
print("ddk/Makefile updated")

# show tail
print("\n".join(s.split("\n")[-12:]))
