#include <linux/module.h>
#include <linux/io.h>
#include <linux/delay.h>
#include <linux/kernel.h>

#define SPM_BASE 0x10006000UL

#define PWR_STATUS      0x180
#define PWR_STATUS_2ND  0x184
#define MFG_CORE0_PWR_CON 0x34c
#define MFG_PWR_CON     0x338
#define MFG_ASYNC_PWR_CON 0x334

#define PWR_RST_B   (1u << 0)
#define PWR_ISO     (1u << 1)
#define PWR_ON      (1u << 2)
#define PWR_ON_2ND  (1u << 3)
#define PWR_CLK_DIS (1u << 4)
#define SRAM_PDN    (1u << 8)
#define SRAM_PDN_ACK (1u << 12)

static void __iomem *s;

static void dump(const char *tag)
{
	pr_info("gpu_diag3[%s]: STATUS=%08x/2ND=%08x CORE0_CON=%08x MFG_CON=%08x ASYNC_CON=%08x\n",
		tag, readl(s + PWR_STATUS), readl(s + PWR_STATUS_2ND),
		readl(s + MFG_CORE0_PWR_CON), readl(s + MFG_PWR_CON),
		readl(s + MFG_ASYNC_PWR_CON));
}

static int __init gd3_init(void)
{
	u32 v;

	s = ioremap(SPM_BASE, 0x1000);
	if (!s) {
		pr_err("gpu_diag3: ioremap failed\n");
		return -ENOMEM;
	}

	dump("before");

	/* vendor sequence: PWR_ON | PWR_ON_2ND */
	v = readl(s + MFG_CORE0_PWR_CON);
	writel(v | PWR_ON | PWR_ON_2ND, s + MFG_CORE0_PWR_CON);
	pr_info("gpu_diag3: wrote %08x -> CORE0_CON=%08x\n",
		v | PWR_ON | PWR_ON_2ND, readl(s + MFG_CORE0_PWR_CON));

	/* poll status up to 200 ms */
	{
		int i;
		for (i = 0; i < 200; i++) {
			u32 st = readl(s + PWR_STATUS);
			u32 st2 = readl(s + PWR_STATUS_2ND);
			if ((st & BIT(7)) && (st2 & BIT(7))) {
				pr_info("gpu_diag3: CORE0 ACK after %d ms\n", i);
				break;
			}
			msleep(1);
		}
		if (i == 200)
			pr_info("gpu_diag3: CORE0 NO ACK after 200 ms\n");
	}
	dump("after-on");

	/* release clk/iso/rst, then SRAM PDN off */
	v = readl(s + MFG_CORE0_PWR_CON);
	v &= ~(PWR_CLK_DIS | PWR_ISO | SRAM_PDN);
	v |= PWR_RST_B;
	writel(v, s + MFG_CORE0_PWR_CON);
	msleep(20);
	dump("after-final");

	return 0;
}

static void __exit gd3_exit(void)
{
	if (s) {
		dump("exit");
		iounmap(s);
	}
}

module_init(gd3_init);
module_exit(gd3_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("force MFG_CORE0 power-on test");
