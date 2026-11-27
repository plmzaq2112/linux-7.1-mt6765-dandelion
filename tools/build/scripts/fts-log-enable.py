p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi/focaltech_common.h"
s = open(p).read()
old = """#define FTS_DEBUG(fmt, args...) ((void)0)
#define FTS_INFO(fmt, args...) ((void)0)
#define FTS_ERROR(fmt, args...) ((void)0)"""
new = """#define FTS_DEBUG(fmt, args...) ((void)0)
#define FTS_INFO(fmt, args...) printk("[FTS_TS]%s:" fmt "\\n", __func__, ##args)
#define FTS_ERROR(fmt, args...) printk("[FTS_TS][E]%s:" fmt "\\n", __func__, ##args)"""
if new not in s:
    assert old in s
    s = s.replace(old, new, 1)
    open(p, "w").write(s)
    print("FTS_INFO/FTS_ERROR enabled")
else:
    print("already")
