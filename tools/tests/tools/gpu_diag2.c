#include <linux/module.h>
#include <linux/io.h>
#include <linux/kernel.h>

#define GPU_BASE   0x13000000UL
#define SPM_BASE   0x10006000UL
#define INFRA_BASE 0x10001000UL

static int __init gd2_init(void)
{
	void __iomem *g = ioremap(GPU_BASE, 0x80000);
	void __iomem *s = ioremap(SPM_BASE, 0x1000);
	void __iomem *i = ioremap(INFRA_BASE, 0x1000);
	u32 pwr, pwr2, prot, protsta, mfg_async, mfg, mfg_c0;

	if (!g || !s || !i) {
		pr_err("gpu_diag2: ioremap failed g=%p s=%p i=%p\n", g, s, i);
		if (g) iounmap(g);
		if (s) iounmap(s);
		if (i) iounmap(i);
		return -ENOMEM;
	}

	pwr      = readl(s + 0x180);
	pwr2     = readl(s + 0x184);
	mfg_async= readl(s + 0x334);
	mfg      = readl(s + 0x338);
	mfg_c0   = readl(s + 0x34c);
	prot     = readl(i + 0x220);
	protsta  = readl(i + 0x228);

	pr_info("gpu_diag2: PWR_STATUS=%08x (MFG=%d CORE0=%d ASYNC=%d)\n",
		pwr, !!(pwr & BIT(4)), !!(pwr & BIT(7)), !!(pwr & BIT(23)));
	pr_info("gpu_diag2: PWR_STATUS_2ND=%08x\n", pwr2);
	pr_info("gpu_diag2: MFG_ASYNC_PWR_CON=%08x MFG_PWR_CON=%08x MFG_CORE0_PWR_CON=%08x\n",
		mfg_async, mfg, mfg_c0);
	pr_info("gpu_diag2: TOPAXI_PROTECTEN=%08x STA1=%08x (mfg step1 bit25=%d step2 bit21=%d)\n",
		prot, protsta, !!(prot & BIT(25)), !!(prot & BIT(21)));

	pr_info("gpu_diag2: CORE_ID=%08x\n", readl(g + 0x18));
	pr_info("gpu_diag2: MIPS_WRAPPER_CONFIG=%016llx\n",
		(unsigned long long)readq(g + 0x810));
	pr_info("gpu_diag2: REMAP1=%016llx/%016llx REMAP2=%016llx/%016llx\n",
		(unsigned long long)readq(g + 0x818), (unsigned long long)readq(g + 0x820),
		(unsigned long long)readq(g + 0x828), (unsigned long long)readq(g + 0x830));
	pr_info("gpu_diag2: REMAP3=%016llx/%016llx\n",
		(unsigned long long)readq(g + 0x838), (unsigned long long)readq(g + 0x840));
	pr_info("gpu_diag2: REMAP4=%016llx/%016llx REMAP5=%016llx/%016llx\n",
		(unsigned long long)readq(g + 0x848), (unsigned long long)readq(g + 0x850),
		(unsigned long long)readq(g + 0x858), (unsigned long long)readq(g + 0x860));
	pr_info("gpu_diag2: MIPS_IRQ_EN=%016llx IRQ_STATUS=%016llx EXC_STATUS=%016llx\n",
		(unsigned long long)readq(g + 0x8a0), (unsigned long long)readq(g + 0x8a8),
		(unsigned long long)readq(g + 0x8d0));

	iounmap(g);
	iounmap(s);
	iounmap(i);
	return 0;
}

static void __exit gd2_exit(void) {}

module_init(gd2_init);
module_exit(gd2_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("GPU/SPM diagnostics");
