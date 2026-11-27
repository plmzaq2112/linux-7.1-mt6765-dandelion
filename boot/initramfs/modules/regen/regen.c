#include <linux/module.h>
#include <linux/regulator/consumer.h>

static char *reg_name = "ldo-vio28";
module_param(reg_name, charp, 0644);
MODULE_PARM_DESC(reg_name, "regulator name to enable");

static struct regulator *reg;

static int __init regen_init(void)
{
	int ret;

	reg = regulator_get(NULL, reg_name);
	if (IS_ERR(reg)) {
		pr_err("regen: regulator %s not found: %ld\n",
		       reg_name, PTR_ERR(reg));
		return PTR_ERR(reg);
	}
	ret = regulator_enable(reg);
	pr_info("regen: %s enable ret=%d enabled=%d\n",
		reg_name, ret, regulator_is_enabled(reg));
	return 0;
}

static void __exit regen_exit(void)
{
	if (!IS_ERR_OR_NULL(reg)) {
		regulator_disable(reg);
		regulator_put(reg);
	}
}

module_init(regen_init);
module_exit(regen_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Enable a named regulator (test)");
