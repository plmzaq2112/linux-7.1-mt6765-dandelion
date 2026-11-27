import re, shutil

V = "/home/a12bbb/dandelion-linux-kernel/01-pure-baseline/drivers/input/touchscreen/ft8006s_spi"
R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi"

shutil.copy2(V + "/focaltech_core.c", R + "/focaltech_core.c")
print("core.c restored from vendor")

p = R + "/focaltech_core.c"
s = open(p).read()

# 1) include of_gpio -> consumer
s = s.replace("#include <linux/of_gpio.h>", "#include <linux/gpio/consumer.h>")

# 2) field names (safe: these are distinct struct members)
s = s.replace("pdata->reset_gpio", "pdata->reset_gpiod")
s = s.replace("pdata->irq_gpio", "pdata->irq_gpiod")

# 3) direction / irq accessors on descriptors
s = s.replace("gpio_direction_output(", "gpiod_direction_output(")
s = s.replace("gpio_direction_input(", "gpiod_direction_input(")
s = s.replace("gpio_to_irq(", "gpiod_to_irq(")

# 4) request/free -> no-op (descriptors managed by devm/fwnode)
s = re.sub(r'\bret = gpio_request\([^;]*\);', 'ret = 0;', s)
s = re.sub(r'\bgpio_free\([^;]*\);', '(void)0;', s)

# 5) of_get_named_gpio_flags blocks -> fwnode_gpiod_get_index
s = re.sub(
    r'(pdata->reset_gpiod\s*=\s*)of_get_named_gpio_flags\(np,\s*"focaltech,reset-gpio",\s*\n\s*0,\s*\(enum of_gpio_flags \*\)&pdata->reset_gpio_flags\);',
    r'\1fwnode_gpiod_get_index(of_fwnode_handle(np), "focaltech,reset", 0, GPIOD_ASIS, "fts_reset");\n'
    '\tif (IS_ERR(pdata->reset_gpiod)) return PTR_ERR(pdata->reset_gpiod);',
    s, count=1)
s = re.sub(
    r'(pdata->irq_gpiod\s*=\s*)of_get_named_gpio_flags\(np,\s*"focaltech,irq-gpio",\s*\n\s*0,\s*\(enum of_gpio_flags \*\)&pdata->irq_gpio_flags\);',
    r'\1fwnode_gpiod_get_index(of_fwnode_handle(np), "focaltech,irq", 0, GPIOD_ASIS, "fts_irq");\n'
    '\tif (IS_ERR(pdata->irq_gpiod)) return PTR_ERR(pdata->irq_gpiod);',
    s, count=1)

# 6) gpio_is_valid(int) -> pointer test
s = s.replace("if (gpio_is_valid(data->pdata->irq_gpiod)) {", "if (data->pdata->irq_gpiod) {")
s = s.replace("if (gpio_is_valid(data->pdata->reset_gpiod)) {", "if (data->pdata->reset_gpiod) {")
s = s.replace("if (gpio_is_valid(data->pdata->reset_gpiod))", "if (data->pdata->reset_gpiod)")
s = s.replace("if (gpio_is_valid(data->pdata->irq_gpiod))", "if (data->pdata->irq_gpiod)")

open(p, "w").write(s)
print("core.c re-patched")

# check leftovers
for pat in ("of_get_named_gpio", "gpio_is_valid", "pdata->reset_gpio\b", "pdata->irq_gpio\b"):
    n = len(re.findall(pat, s))
    print("leftover", pat, n)
