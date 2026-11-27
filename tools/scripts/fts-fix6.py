p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi/focaltech_core.c"
s = open(p).read()

guard = '''/* 7.1 dropped the fbdev blank notifier events; define them so the
 * (unused, no fbdev in this kernel) notifier compiles. */
#ifndef FB_EARLY_EVENT_BLANK
#define FB_EARLY_EVENT_BLANK 0x10
#endif
#ifndef FB_EVENT_BLANK
#define FB_EVENT_BLANK 0x09
#endif

'''

# remove old guard wherever it is
import re
s = re.sub(r'/\* 7\.1 dropped the fbdev blank notifier events;.*?#endif\n#endif\n\n', '', s, flags=re.S)

# insert right before the focaltech_core.h include
anchor = '#include "focaltech_core.h"'
assert anchor in s
s = s.replace(anchor, guard + anchor, 1)
open(p, "w").write(s)
print("guard relocated")
