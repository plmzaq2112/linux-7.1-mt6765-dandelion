R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline"

# Makefile
p = R + "/drivers/input/touchscreen/Makefile"
s = open(p).read()
if "ft8006s_spi/" not in s:
    s = s.rstrip("\n") + "\nobj-$(CONFIG_TOUCHSCREEN_FTS)\t+= ft8006s_spi/\n"
    open(p, "w").write(s)
    print("Makefile: added ft8006s_spi")
else:
    print("Makefile: already")

# Kconfig
p = R + "/drivers/input/touchscreen/Kconfig"
s = open(p).read()
if "config TOUCHSCREEN_FTS" not in s:
    entry = '''
config TOUCHSCREEN_FTS
\ttristate "FocalTech FT8006S SPI touchscreen"
\tdepends on SPI
\thelp
\t  Say Y here to enable the FocalTech FT8006S SPI touchscreen
\t  (used on Xiaomi Redmi 9A / dandelion).

\t  If unsure, say N.
'''
    # insert before the final 'endif'
    idx = s.rfind("endif")
    assert idx > 0
    s = s[:idx] + entry + "\n" + s[idx:]
    open(p, "w").write(s)
    print("Kconfig: added TOUCHSCREEN_FTS")
else:
    print("Kconfig: already")
