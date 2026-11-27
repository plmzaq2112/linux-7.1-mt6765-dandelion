import os, re

root = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk")
p = os.path.join(root, "services/server/devices/rogue/rgxfwutils.c")
lines = open(p, errors="replace").read().split("\n")
for i, l in enumerate(lines, 1):
    if "__MTSScheduleWrite" in l and ("static" in l or "void" in l):
        print("\n".join(f"{j}: {lines[j-1]}" for j in range(i, min(i + 22, len(lines)))))
        break
