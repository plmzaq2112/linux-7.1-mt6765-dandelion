R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/input/touchscreen/ft8006s_spi"
p = R + "/focaltech_core.c"
s = open(p).read()

guard = '''
/* 7.1 dropped the fbdev blank notifier events; define them so the
 * (unused, no fbdev in this kernel) notifier compiles. */
#ifndef FB_EARLY_EVENT_BLANK
#define FB_EARLY_EVENT_BLANK 0x10
#endif
#ifndef FB_EVENT_BLANK
#define FB_EVENT_BLANK 0x09
#endif
'''

if "7.1 dropped the fbdev blank notifier" not in s:
    # insert after the last #include line
    idx = s.rfind("#include")
    eol = s.find("\n", idx)
    s = s[:eol+1] + guard + s[eol+1:]
    open(p, "w").write(s)
    print("guards inserted")
else:
    print("already")
