// SPDX-License-Identifier: GPL-2.0
/*
 * Debug helper: enable/disable a named regulator from userspace so an unused
 * peripheral rail can be powered while probing its I2C bus.
 *
 *   insmod rail_en.ko name=vcn28
 *   rmmod rail_en
 */
#include <linux/module.h>
#include <linux/regulator/consumer.h>

static char *name = "vcn28";
module_param(name, charp, 0444);
MODULE_PARM_DESC(name, "regulator name to enable");

static struct regulator *rail;

static int __init rail_en_init(void)
{
	int ret;

	rail = regulator_get(NULL, name);
	if (IS_ERR(rail)) {
		pr_err("rail_en: regulator_get(%s) failed: %ld\n", name, PTR_ERR(rail));
		return PTR_ERR(rail);
	}

	ret = regulator_enable(rail);
	pr_info("rail_en: %s enable ret=%d\n", name, ret);
	return ret;
}

static void __exit rail_en_exit(void)
{
	if (!IS_ERR_OR_NULL(rail)) {
		regulator_disable(rail);
		regulator_put(rail);
	}
	pr_info("rail_en: %s disabled\n", name);
}

module_init(rail_en_init);
module_exit(rail_en_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Enable a named regulator for I2C bring-up probing");
