R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = R + "/services/server/devices/rogue/rgxinit.c"
s = open(p).read()
old = "\t         (unsigned long long)RGX_FIRMWARE_RAW_HEAP_BASE));\n"
new = "\t         (unsigned long long)RGX_FIRMWARE_RAW_HEAP_BASE);\n"
assert old in s
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("fixed")
