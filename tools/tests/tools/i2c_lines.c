// SPDX-License-Identifier: GPL-2.0
/*
 * Debug helper: read raw pad levels of given GPIO pins (I2C line state).
 *
 *   insmod i2c_lines.ko pins=50,51
 */
#include <linux/gpio.h>
#include <linux/module.h>

static char *pins = "50,51";
module_param(pins, charp, 0444);

static int __init i2c_lines_init(void)
{
	char *p = pins;

	while (p && *p) {
		int n = simple_strtol(p, &p, 10);
		int ret;

		ret = gpio_request(n, "i2c_line_probe");
		if (ret) {
			pr_info("i2c_lines: gpio %d request failed %d\n", n, ret);
		} else {
			gpio_direction_input(n);
			pr_info("i2c_lines: gpio %d level=%d\n", n, gpio_get_value(n));
			gpio_free(n);
		}
		if (*p == ',')
			p++;
		else if (*p)
			break;
	}
	return 0;
}

static void __exit i2c_lines_exit(void) {}

module_init(i2c_lines_init);
module_exit(i2c_lines_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Read I2C line levels via GPIO input buffers");
