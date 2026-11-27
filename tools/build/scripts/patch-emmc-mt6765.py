#!/usr/bin/env python3
"""Port the m3 eMMC fix to this tree (driver flags only; the boot DTB is r96,
which already carries the DTS side: top regs, pad group, HS400, clock fix).

Reference (read-only): mt6765-mainline-m3/CHANGES.md r16 + r17.
"""
import shutil

p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/mmc/host/mtk-sd.c"
shutil.copyfile(p, p + ".r3-before")
s = open(p).read()

old = """static const struct mtk_mmc_compatible mt6765_compat = {
\t.clk_div_bits = 12,
\t.recheck_sdio_irq = false,
\t.hs400_tune = false,
\t.pad_tune_reg = MSDC_PAD_TUNE0,
\t.async_fifo = true,
\t.data_tune = false,"""
new = """static const struct mtk_mmc_compatible mt6765_compat = {
\t.clk_div_bits = 12,
\t.recheck_sdio_irq = false,
\t.hs400_tune = false,
\t.pad_tune_reg = MSDC_PAD_TUNE0,
\t.async_fifo = true,
\t.needs_top_base = true,
\t.data_tune = true,"""

if s.count(old) != 1:
    raise SystemExit("pattern count = %d, aborting" % s.count(old))
open(p, "w").write(s.replace(old, new))
print("patched mt6765_compat: needs_top_base=true, data_tune=true")
