import os, sys

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline"
A = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/artifacts"

# 1. driver source
src = open(os.path.join(A, "panel-fitipower-ft8006s.c")).read()
open(os.path.join(R, "drivers/gpu/drm/panel/panel-fitipower-ft8006s.c"), "w").write(src)

# 2. Kconfig
kp = os.path.join(R, "drivers/gpu/drm/panel/Kconfig")
k = open(kp).read()
if "DRM_PANEL_FITIPOWER_FT8006S" not in k:
    entry = '''config DRM_PANEL_FITIPOWER_FT8006S
\ttristate "Fitipower FT8006S"
\tdepends on OF
\tdepends on DRM_MIPI_DSI
\thelp
\t  Say Y here if you want to enable support for the Fitipower FT8006S
\t  DSI panel (Redmi 9A / dandelion).

'''
    k = k.replace("\nendmenu", "\n" + entry + "endmenu")
    open(kp, "w").write(k)
    print("Kconfig updated")
else:
    print("Kconfig already has entry")

# 3. Makefile
mp = os.path.join(R, "drivers/gpu/drm/panel/Makefile")
m = open(mp).read()
if "panel-fitipower-ft8006s" not in m:
    m += "obj-$(CONFIG_DRM_PANEL_FITIPOWER_FT8006S) += panel-fitipower-ft8006s.o\n"
    open(mp, "w").write(m)
    print("Makefile updated")
else:
    print("Makefile already has entry")

# 4. defconfig
dp = os.path.join(R, "arch/arm64/configs/dandelion_defconfig")
d = open(dp).read()
if "DRM_PANEL_FITIPOWER_FT8006S" not in d:
    d += "\n# FT8006S panel\nCONFIG_DRM_PANEL_FITIPOWER_FT8006S=y\n"
    open(dp, "w").write(d)
    print("defconfig updated")
else:
    print("defconfig already has entry")
