import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()
s = s.replace("mdelay(20);", "OSWaitus(20000);")
open(P, "w").write(s)
print("replaced:", s.count("OSWaitus(20000)"))
