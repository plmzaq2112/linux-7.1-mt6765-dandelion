#include <linux/module.h>
#include <linux/io.h>
#include <linux/kernel.h>

#define GPU_BASE 0x13000000UL

static int __init gd_init(void)
{
	void __iomem *b = ioremap(GPU_BASE, 0x80000);

	if (!b) {
		pr_err("gpu_diag: ioremap failed\n");
		return -ENOMEM;
	}

	pr_info("gpu_diag: core_id=%08x\n", readl(b + 0x18));
	pr_info("gpu_diag: bif_cat0=%016llx bif_cat1=%016llx\n",
		(unsigned long long)readq(b + 0x1200),
		(unsigned long long)readq(b + 0x1208));
	pr_info("gpu_diag: mmu_fault=%016llx mmu_cbase=%016llx\n",
		(unsigned long long)readq(b + 0xE150),
		(unsigned long long)readq(b + 0xE148));
	pr_info("gpu_diag: garten=%016llx clk_ctrl=%016llx\n",
		(unsigned long long)readq(b + 0xB50),
		(unsigned long long)readq(b + 0x0));
	pr_info("gpu_diag: soft_reset=%016llx meta_boot=%08x mslvctrl1=%08x\n",
		(unsigned long long)readq(b + 0x100),
		readl(b + 0xBF8), readl(b + 0xA18));

	iounmap(b);
	return 0;
}

static void __exit gd_exit(void)
{
}

module_init(gd_init);
module_exit(gd_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("one-shot GPU register dump");
