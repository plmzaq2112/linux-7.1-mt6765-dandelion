#include <linux/module.h>
#include <linux/io.h>
#include <linux/kernel.h>

#define GPU_BASE 0x13000000UL

static u64 rd64(void __iomem *b, unsigned off)
{
	return readq(b + off);
}

static int __init gd4_init(void)
{
	void __iomem *g = ioremap(GPU_BASE, 0x80000);

	if (!g) {
		pr_err("gpu_diag4: ioremap failed\n");
		return -ENOMEM;
	}

	pr_info("gpu_diag4: EXC_STATUS=%016llx REMAP_UNMAPPED=%016llx\n",
		rd64(g, 0x8d0), rd64(g, 0x868));
	pr_info("gpu_diag4: REMAP_RANGE_CFG=%016llx REMAP_RANGE_READ=%016llx DATA=%016llx\n",
		rd64(g, 0x878), rd64(g, 0x880), rd64(g, 0x888));
	pr_info("gpu_diag4: IRQ_EN=%016llx IRQ_STATUS=%016llx DEBUG_CFG=%016llx\n",
		rd64(g, 0x8a0), rd64(g, 0x8a8), rd64(g, 0x8c8));
	pr_info("gpu_diag4: META_BOOT=%08x MSLVCTRL1=%08x SOFT_RESET=%016llx\n",
		readl(g + 0xbf8), readl(g + 0xa18), rd64(g, 0x100));
	pr_info("gpu_diag4: WRAPPER=%016llx REMAP1=%016llx/%016llx\n",
		rd64(g, 0x810), rd64(g, 0x818), rd64(g, 0x820));
	pr_info("gpu_diag4: CORE_ID=%08x CLK_CTRL=%016llx CLK_STATUS=%016llx\n",
		readl(g + 0x18), rd64(g, 0x0), rd64(g, 0x8));

	iounmap(g);
	return 0;
}

static void __exit gd4_exit(void) {}

module_init(gd4_init);
module_exit(gd4_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("MIPS exception/remap diagnostics");
