// SPDX-License-Identifier: GPL-2.0
/*
 * Debug helper: enable one or more named regulators from userspace.
 *
 *   insmod rail_en.ko names=vcn18,vcn28,vldo28
 *   rmmod rail_en
 */
#include <linux/module.h>
#include <linux/regulator/consumer.h>

#define MAX_RAILS 16

static char *names[MAX_RAILS];
static int num_names;
module_param_array(names, charp, &num_names, 0444);
MODULE_PARM_DESC(names, "comma separated regulator names to enable");

static struct regulator *rails[MAX_RAILS];

static int __init rail_en_init(void)
{
	int i, ret, ok = 0;

	if (!num_names) {
		pr_err("rail_en: no names given\n");
		return -EINVAL;
	}

	for (i = 0; i < num_names && i < MAX_RAILS; i++) {
		rails[i] = regulator_get(NULL, names[i]);
		if (IS_ERR(rails[i])) {
			pr_err("rail_en: get %s failed %ld\n", names[i],
			       PTR_ERR(rails[i]));
			rails[i] = NULL;
			continue;
		}
		ret = regulator_enable(rails[i]);
		pr_info("rail_en: %s enable ret=%d\n", names[i], ret);
		if (!ret)
			ok++;
	}
	pr_info("rail_en: %d/%d rails on\n", ok, num_names);
	return ok ? 0 : -ENODEV;
}

static void __exit rail_en_exit(void)
{
	int i;

	for (i = 0; i < MAX_RAILS; i++) {
		if (!rails[i])
			continue;
		regulator_disable(rails[i]);
		regulator_put(rails[i]);
	}
	pr_info("rail_en: rails disabled\n");
}

module_init(rail_en_init);
module_exit(rail_en_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Enable named regulators for I2C bring-up probing");
