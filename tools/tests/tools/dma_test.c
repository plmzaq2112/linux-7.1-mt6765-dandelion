#include <linux/module.h>
#include <linux/device.h>
#include <linux/dma-mapping.h>
#include <linux/platform_device.h>

static int __init dmat_init(void)
{
	struct device *dev;
	dma_addr_t addr = 0;
	void *va;
	int i;

	dev = bus_find_device_by_name(&platform_bus_type, NULL, "13000000.mfg_doma");
	if (!dev) {
		pr_err("dmat: gpu platform device not found\n");
		return -ENODEV;
	}

	pr_info("dmat: dev=%s dma_mask=%#llx coherent_mask=%#llx\n",
		dev_name(dev),
		(unsigned long long)(dev->dma_mask ? *dev->dma_mask : 0),
		(unsigned long long)dev->coherent_dma_mask);

	for (i = 0; i < 4; i++) {
		va = dma_alloc_coherent(dev, 65536, &addr, GFP_KERNEL);
		pr_info("dmat: alloc #%d va=%px dma=0x%llx\n", i, va,
			(unsigned long long)addr);
		if (va)
			dma_free_coherent(dev, 65536, va, addr);
	}

	return 0;
}

static void __exit dmat_exit(void)
{
}

module_init(dmat_init);
module_exit(dmat_exit);
MODULE_LICENSE("GPL");
