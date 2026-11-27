#include <linux/module.h>
#include <linux/io.h>
#include <linux/kernel.h>
#include <linux/ioport.h>

static unsigned long addr = 0x7cd27000;
static int addr_param_set;
module_param(addr, ulong, 0444);

static int __init fwchk_init(void)
{
	void *p;
	int i;

	pr_info("fwchk: probing phys 0x%lx (page 0x%lx)\n", addr, addr & PAGE_MASK);

	p = memremap(addr & PAGE_MASK, 0x100, MEMREMAP_WB);
	if (!p) {
		pr_err("fwchk: memremap failed\n");
		return -ENOMEM;
	}

	pr_info("fwchk: @0x%lx magic-ish:", addr & PAGE_MASK);
	for (i = 0; i < 32; i += 4)
		pr_info("fwchk:   [%02x] %08x", i, readl((char *)p + i));

	iounmap(p);
	return 0;
}

static void __exit fwchk_exit(void)
{
}

module_init(fwchk_init);
module_exit(fwchk_exit);
MODULE_LICENSE("GPL");
