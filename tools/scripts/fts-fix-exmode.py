p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi/focaltech_ex_mode.c"
s = open(p).read()
old = 'FTS_INFO("charger mode:%d", ts_data->charger_mode);'
new = 'FTS_INFO("charger mode done");'
assert old in s
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("fixed charger log")
