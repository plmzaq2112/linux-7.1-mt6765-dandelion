#include <linux/module.h>
#include <linux/gpio.h>
#include <linux/delay.h>

#define AMP_EN_GPIO 665

static int __init amp_en_init(void)
{
	int ret, i;

	ret = gpio_request(AMP_EN_GPIO, "speaker-amp-en");
	if (ret) {
		pr_err("speaker-amp-en: gpio_request(%d) failed: %d\n",
		       AMP_EN_GPIO, ret);
		return ret;
	}

	/* vendor AudDrv_GPIO_EXTAMP_Select(): LOW -> HIGH pulses, then HIGH */
	ret = gpio_direction_output(AMP_EN_GPIO, 0);
	if (ret)
		goto err;
	for (i = 0; i < 3; i++) {
		udelay(2);
		gpio_set_value(AMP_EN_GPIO, 1);
		udelay(2);
		gpio_set_value(AMP_EN_GPIO, 0);
	}
	udelay(2);
	gpio_set_value(AMP_EN_GPIO, 1);

	pr_info("speaker-amp-en: GPIO %d pulsed, left high\n", AMP_EN_GPIO);
	return 0;
err:
	gpio_free(AMP_EN_GPIO);
	return ret;
}

static void __exit amp_en_exit(void)
{
	gpio_set_value(AMP_EN_GPIO, 0);
	gpio_free(AMP_EN_GPIO);
	pr_info("speaker-amp-en: GPIO %d low\n", AMP_EN_GPIO);
}

module_init(amp_en_init);
module_exit(amp_en_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Dandelion speaker amp enable test");
