#include <linux/module.h>
#include <linux/gpio.h>

#define I2C3_SCL 562	/* global = 512 + pin 50 */
#define I2C3_SDA 563	/* global = 512 + pin 51 */

static int __init pinstat_init(void)
{
	int ret;

	ret = gpio_request(I2C3_SCL, "i2c3-scl");
	if (ret) {
		pr_err("pinstat: SCL request failed %d\n", ret);
		return ret;
	}
	ret = gpio_request(I2C3_SDA, "i2c3-sda");
	if (ret) {
		pr_err("pinstat: SDA request failed %d\n", ret);
		gpio_free(I2C3_SCL);
		return ret;
	}
	gpio_direction_input(I2C3_SCL);
	gpio_direction_input(I2C3_SDA);
	pr_info("pinstat: i2c3 SCL=%d SDA=%d\n",
		gpio_get_value(I2C3_SCL), gpio_get_value(I2C3_SDA));
	return 0;
}

static void __exit pinstat_exit(void)
{
	gpio_free(I2C3_SDA);
	gpio_free(I2C3_SCL);
}

module_init(pinstat_init);
module_exit(pinstat_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Dandelion i2c3 pin level probe");
