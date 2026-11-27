import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/hwdefs/rogue/km/rgx_bvnc_table_km.h")
s = open(P).read()
old = "/* 22.0.104.18 (PHYS_BUS_WIDTH forced 32) */"
new = "/* 22.0.104.18 (36-bit; bus=32 was tried and did NOT fix FW boot) */"
if old in s:
    s = s.replace(old, new)
    open(P, "w").write(s)
    print("comment fixed")
else:
    print("comment already updated")
