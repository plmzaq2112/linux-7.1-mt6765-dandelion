import struct, subprocess, os

BASE = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-power8.img"
KERN = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/out/arch/arm64/boot/Image.gz"
OUT = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-audio1.img"
WORK = "/tmp/au"
os.makedirs(WORK, exist_ok=True)

d = open(BASE, "rb").read()
page = struct.unpack_from("<I", d, 36)[0]
hv = struct.unpack_from("<I", d, 40)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
ds = struct.unpack_from("<I", d, 1648)[0]
au = lambda x, p: ((x + p - 1) // p) * p
k_off = page
rd_off = k_off + au(ks, page)
dt_off = rd_off + au(rs, page)
ramdisk = d[rd_off:rd_off+rs]
dtb = d[dt_off:dt_off+ds]
open(f"{WORK}/base.dtb", "wb").write(dtb)

subprocess.run(["dtc", "-I", "dtb", "-O", "dts", f"{WORK}/base.dtb", "-o", f"{WORK}/base.dts"],
               check=True, stderr=subprocess.DEVNULL)
lines = open(f"{WORK}/base.dts").read().splitlines()

# find the mt6357 auxadc compatible, then the enclosing adc node opening line
idx = None
for i, l in enumerate(lines):
    if 'compatible = "mediatek,mt6357-auxadc";' in l:
        idx = i
        break
assert idx is not None, "auxadc compatible not found"

adc_open = None
for j in range(idx, max(0, idx - 6), -1):
    if lines[j].strip() == "adc {":
        adc_open = j
        break
assert adc_open is not None, "adc node open not found"
print("inserting before line", adc_open + 1, ":", lines[adc_open])

node = [
    "\t\t\t\tsound {",
    '\t\t\t\t\tcompatible = "mediatek,mt6357-sound";',
    "\t\t\t\t\tvaud28-supply = <0x8a>;",
    "\t\t\t\t};",
    "",
]
lines[adc_open:adc_open] = node
open(f"{WORK}/new.dts", "w").write("\n".join(lines) + "\n")

subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", f"{WORK}/new.dtb", f"{WORK}/new.dts"],
               check=True, stderr=subprocess.DEVNULL)
newdtb = open(f"{WORK}/new.dtb", "rb").read()
print("dtb", len(dtb), "->", len(newdtb))

kernel = open(KERN, "rb").read()
hdr = bytearray(d[:page])
struct.pack_into("<I", hdr, 8, len(kernel))
struct.pack_into("<I", hdr, 16, len(ramdisk))
struct.pack_into("<I", hdr, 24, 0)
if hv >= 2:
    struct.pack_into("<I", hdr, 1648, len(newdtb))

buf = bytearray()
buf += hdr
buf += kernel
buf += b"\x00" * (au(len(buf), page) - len(buf))
buf += ramdisk
buf += b"\x00" * (au(len(buf), page) - len(buf))
buf += newdtb
buf += b"\x00" * (au(len(buf), page) - len(buf))
if len(buf) < len(d):
    buf += b"\x00" * (len(d) - len(buf))
open(OUT, "wb").write(buf)
print("wrote", OUT, len(buf))
