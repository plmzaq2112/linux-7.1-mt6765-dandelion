import os

base = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk")

def show(path, a, b):
    p = os.path.join(base, path)
    lines = open(p, errors="replace").read().split("\n")
    for i in range(a - 1, min(b, len(lines))):
        print(f"{i+1}: {lines[i]}")

print("===== rgx_fw_info.h (FW_INFO_VERSION + struct)")
p = os.path.join(base, "services/include/rgx_fw_info.h")
txt = open(p, errors="replace").read().split("\n")
for i, l in enumerate(txt, 1):
    if "FW_INFO_VERSION" in l or "typedef struct" in l or "} " in l and "INFO" in l:
        print(f"{i}: {l}")

print("\n===== rgx_fw_info.h lines 80-140")
show("services/include/rgx_fw_info.h", 80, 140)

print("\n===== rgxfwimageutils.c 730-800")
show("services/server/devices/rogue/rgxfwimageutils.c", 730, 800)
