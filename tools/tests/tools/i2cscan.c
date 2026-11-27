// SPDX-License-Identifier: GPL-2.0
/*
 * Debug helper: scan i2c buses for responding addresses from kernel context.
 *
 *   insmod i2cscan.ko buses=0,1,2,3,4,5,6
 *   dmesg | grep i2cscan
 */
#include <linux/i2c.h>
#include <linux/module.h>

static char *buses = "0,1,2,3,4,5,6";
module_param(buses, charp, 0444);

static int scan_one(struct i2c_adapter *adap, u16 addr)
{
	u8 reg = 0x0f;
	struct i2c_msg msg = {
		.addr = addr,
		.flags = 0,
		.len = 1,
		.buf = &reg,
	};

	return i2c_transfer(adap, &msg, 1);
}

static int __init i2cscan_init(void)
{
	char *p = buses;
	int nack = 0, ack = 0, err = 0;

	while (p && *p) {
		int bus = simple_strtol(p, &p, 10);
		struct i2c_adapter *adap = i2c_get_adapter(bus);
		u16 addr;

		if (!adap) {
			pr_info("i2cscan: bus %d missing\n", bus);
		} else {
			nack = ack = err = 0;
			for (addr = 0x08; addr < 0x78; addr++) {
				int ret = scan_one(adap, addr);

				if (ret == 1) {
					pr_info("i2cscan: bus %d ACK 0x%02x\n", bus, addr);
					ack++;
				} else if (ret == -ENXIO || ret == -EREMOTEIO) {
					nack++;
				} else {
					pr_info("i2cscan: bus %d addr 0x%02x err %d\n",
						bus, addr, ret);
					err++;
				}
			}
			pr_info("i2cscan: bus %d done ack=%d nack=%d err=%d\n",
				bus, ack, nack, err);
			i2c_put_adapter(adap);
		}
		if (*p == ',')
			p++;
		else if (*p)
			break;
	}
	return 0;
}

static void __exit i2cscan_exit(void) {}

module_init(i2cscan_init);
module_exit(i2cscan_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("I2C bus scanner for bring-up");
