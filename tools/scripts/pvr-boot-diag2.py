R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

p = R + "/services/server/devices/rogue/rgxpower.c"
s = open(p).read()
i = s.find("pvr-mtk: boot stage")
assert i > 0
# replace the PVR_LOG( ( ... ) ); wrapper with pr_info( ... );
start = s.rfind("PVR_LOG((", 0, i)
assert start > 0
end = s.find(")));", i)
assert end > 0
block = s[start:end + 4]
inner = block[len("PVR_LOG(("):-3]          # drop PVR_LOG((  and  )));
s = s[:start] + "pr_info(" + inner + ");" + s[end + 4:]
open(p, "w").write(s)
print("rgxpower ok")

p = R + "/services/server/devices/rogue/rgxinit.c"
s = open(p).read()
i = s.find("pvr-mtk: fw code DevVAddr")
assert i > 0
start = s.rfind("PVR_LOG((", 0, i)
assert start > 0
end = s.find("));", i)
assert end > 0
block = s[start:end + 3]
inner = block[len("PVR_LOG(("):-2]
inner = inner.replace('%"IMG_UINT64_FMTSPECx" (want %"IMG_UINT64_FMTSPECx")', '%llx (want %llx)')
inner = inner.replace("(IMG_UINT64)", "(unsigned long long)")
s = s[:start] + "pr_info(" + inner + ");" + s[end + 3:]
open(p, "w").write(s)
print("rgxinit ok")
