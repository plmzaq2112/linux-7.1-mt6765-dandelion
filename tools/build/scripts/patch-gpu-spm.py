#!/usr/bin/env python3
"""Add SPM/MTCMOS sampling points around the FW boot attempt.

Idempotent: re-running does nothing if the markers are present.
"""
import os
import sys

R = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline")
PLAT = os.path.join(R, "drivers/misc/pvr/ddk/services/system/rogue/rgx_mtk/pvr_platform_mt6765.c")
PWR = os.path.join(R, "drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")

FUNC = r'''
/*
 * Debug helper: sample the SPM MTCMOS state at FW boot time.
 * MFG_CORE0 (bit 7 of PWR_STATUS) is the domain the MIPS lives in.
 */
void mtk_pvr_dump_spm(const char *tag)
{
	static void __iomem *spm;
	u32 st, st2, c0, mfg, async;

	if (!spm)
		spm = ioremap(0x10006000, 0x1000);
	if (!spm)
		return;

	st    = readl(spm + 0x180);
	st2   = readl(spm + 0x184);
	c0    = readl(spm + 0x34c);
	mfg   = readl(spm + 0x338);
	async = readl(spm + 0x334);

	pr_info("pvr-mtk[%s]: SPM st=%08x/2nd=%08x MFG=%d CORE0=%d ASYNC=%d CORE0_CON=%08x MFG_CON=%08x ASYNC_CON=%08x\n",
		tag, st, st2, !!(st & BIT(4)), !!(st & BIT(7)), !!(st & BIT(23)),
		c0, mfg, async);
}
'''

DECL = "extern void mtk_pvr_dump_spm(const char *tag);\n"


def patch_platform():
    s = open(PLAT).read()
    if "mtk_pvr_dump_spm" in s:
        print("platform: already patched")
        return
    # append the helper at the end of the file
    s = s.rstrip() + "\n" + FUNC
    open(PLAT, "w").write(s)
    print("platform: helper appended")


def patch_rgxpower():
    s = open(PWR).read()
    if DECL in s:
        print("rgxpower: already patched")
        return

    # 1) declaration + macro helpers after the last #include line
    idx = s.rfind("#include")
    if idx < 0:
        sys.exit("rgxpower: no #include found")
    end = s.find("\n", idx) + 1
    s = s[:end] + "\n" + DECL + "\n" + s[end:]

    # 2) sample right before RGXDoStart and after it (before the poll)
    anchor = "eError = RGXDoStart(psDeviceNode);"
    n = s.count(anchor)
    if n != 1:
        sys.exit("rgxpower: RGXDoStart anchor count=%d" % n)
    s = s.replace(anchor, 'mtk_pvr_dump_spm("pre-start");\n\t\t\t' + anchor)

    anchor2 = "OSMemoryBarrier();"
    n = s.count(anchor2)
    if n < 1:
        sys.exit("rgxpower: OSMemoryBarrier anchor not found")
    # only the one directly after RGXDoStart: replace the first occurrence after the start call
    pos = s.find(anchor)
    pos2 = s.find(anchor2, pos)
    if pos2 < 0:
        sys.exit("rgxpower: OSMemoryBarrier after start not found")
    s = s[:pos2] + 'mtk_pvr_dump_spm("post-start");\n\t\t\t' + s[pos2:]

    open(PWR, "w").write(s)
    print("rgxpower: patched")


patch_platform()
patch_rgxpower()
