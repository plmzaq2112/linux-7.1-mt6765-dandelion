import struct, subprocess, re, os

BOOT = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-keys2.img"
KERN = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/out/arch/arm64/boot/Image.gz"
OUT = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-power7.img"
WORK = "/tmp/pw"
os.makedirs(WORK, exist_ok=True)

d = open(BOOT, "rb").read()
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
text = open(f"{WORK}/base.dts").read()

phandles = [int(x, 16) for x in re.findall(r"phandle = <0x([0-9a-fA-F]+)>", text)]
newph = max(phandles) + 1
print("max phandle", hex(max(phandles)), "new", hex(newph))

nodes = f"""
\tbattery {{
\t\tcompatible = "simple-battery";
\t\tvoltage-min-design-microvolt = <3400000>;
\t\tvoltage-max-design-microvolt = <4400000>;
\t\tcharge-full-design-microamp-hours = <5000000>;
\t\tocv-capacity-table-0 = <4380000 100 4300000 95 4200000 88 4100000 78 4000000 66 3900000 54 3800000 42 3750000 35 3700000 28 3650000 20 3600000 12 3550000 6 3450000 2 3400000 0>;
\t\tocv-capacity-celsius = <25>;
\t\tphandle = <0x{newph:x}>;
\t}};

\tadc-battery {{
\t\tcompatible = "adc-battery";
\t\tio-channels = <0x76 0x00>;
\t\tio-channel-names = "voltage";
\t\tmonitored-battery = <0x{newph:x}>;
\t}};
"""

idx = text.rstrip().rfind("};")
assert idx > 0
text = text[:idx] + nodes + text[idx:]
open(f"{WORK}/new.dts", "w").write(text)

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
