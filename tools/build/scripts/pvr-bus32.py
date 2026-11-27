p = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/hwdefs/rogue/km/rgx_bvnc_table_km.h"
s = open(p).read()

old = "{ IMG_UINT64_C(0x0016000000680012), IMG_UINT64_C(0x00000045844e600b), IMG_UINT64_C(0x0008d28253100100) },\t/* 22.0.104.18 */"
new = "{ IMG_UINT64_C(0x0016000000680012), IMG_UINT64_C(0x00000045844e600b), IMG_UINT64_C(0x0008d28353100100) },\t/* 22.0.104.18 (PHYS_BUS_WIDTH forced 32) */"

if "PHYS_BUS_WIDTH forced 32" in s:
    print("already patched")
else:
    assert old in s, "entry not found"
    s = s.replace(old, new, 1)
    open(p, "w").write(s)
    print("PHYS_BUS_WIDTH -> 32")
