p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi/fts_stub.c"
s = open(p).read()
s = s.replace('void lct_tp_selftest_init(void *callback) {}',
              'void lct_tp_selftest_init(tp_selftest_callback_t callback) {}')
if '#include "../lct_tp_selftest.h"' not in s:
    s = s.replace('#include "focaltech_core.h"',
                  '#include "focaltech_core.h"\n#include "../lct_tp_selftest.h"', 1)
open(p, "w").write(s)
print("stub fixed")
