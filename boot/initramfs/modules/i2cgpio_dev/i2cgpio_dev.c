#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/platform_data/i2c-gpio.h>
#include <linux/gpio/machine.h>

#define I2C3_SCL 50
#define I2C3_SDA 51

static struct gpiod_lookup_table i2c3_gpio_lookup = {
	.dev_id = "i2c-gpio.3",
	.table = {
		GPIO_LOOKUP("pinctrl_paris", I2C3_SDA, "sda",
			    GPIO_ACTIVE_HIGH),
		GPIO_LOOKUP("pinctrl_paris", I2C3_SCL, "scl",
			    GPIO_ACTIVE_HIGH),
		{ }
	},
};

static struct i2c_gpio_platform_data i2c3_gpio_pdata = {
	.udelay = 5,
	.timeout = 100,
};

static struct platform_device i2c3_gpio_pdev = {
	.name = "i2c-gpio",
	.id = 3,
	.dev = {
		.platform_data = &i2c3_gpio_pdata,
	},
};

static int __init i2c3_gpio_dev_init(void)
{
	int ret;

	gpiod_add_lookup_table(&i2c3_gpio_lookup);
	ret = platform_device_register(&i2c3_gpio_pdev);
	if (ret)
		gpiod_remove_lookup_table(&i2c3_gpio_lookup);
	return ret;
}

static void __exit i2c3_gpio_dev_exit(void)
{
	platform_device_unregister(&i2c3_gpio_pdev);
	gpiod_remove_lookup_table(&i2c3_gpio_lookup);
}

module_init(i2c3_gpio_dev_init);
module_exit(i2c3_gpio_dev_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Dandelion i2c3 bit-banged bus (GPIO 50/51)");
