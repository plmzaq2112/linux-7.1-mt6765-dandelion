R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = R + "/services/system/rogue/rgx_mtk/pvr_platform_mt6765.c"
s = open(p).read()

# need dma-mapping for DMA_BIT_MASK
if "#include <linux/dma-mapping.h>" not in s:
    s = s.replace("#include <linux/pm_runtime.h>",
                  "#include <linux/pm_runtime.h>\n#include <linux/dma-mapping.h>", 1)

anchor = """\t/* power domains are described in DT; make sure they are on */
\tpm_runtime_enable(dev);
"""
add = """\t/* The MIPS firmware processor is 32-bit: keep its FW/CMA memory below 4GB */
\tret = dma_set_mask_and_coherent(dev, DMA_BIT_MASK(32));
\tdev_info(dev, "pvr-mtk: dma_set_mask(32)=%d\\n", ret);

""" + anchor
if "dma_set_mask(32)" not in s:
    assert anchor in s
    s = s.replace(anchor, add, 1)
    open(p, "w").write(s)
    print("dma mask 32 added")
else:
    print("already")
