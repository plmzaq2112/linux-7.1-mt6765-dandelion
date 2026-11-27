import struct, subprocess, os, re

BASE = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-power8.img"
KERN = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/out/arch/arm64/boot/Image.gz"
OUT = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-audio2.img"
WORK = "/tmp/au2"
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
text = open(f"{WORK}/base.dts").read()
lines = text.splitlines()

maxph = max(int(x, 16) for x in re.findall(r"phandle = <0x([0-9a-fA-F]+)>", text))
afe_ph = maxph + 1
print("afe phandle", hex(afe_ph))

# --- 1. codec node under pmic (before the mt6357 auxadc node) ---
idx = next(i for i, l in enumerate(lines) if 'compatible = "mediatek,mt6357-auxadc";' in l)
adc_open = next(j for j in range(idx, max(0, idx - 6), -1) if lines[j].strip() == "adc {")
codec = [
    "\t\t\t\taudio-codec {",
    '\t\t\t\t\tcompatible = "mediatek,mt6357-sound";',
    "\t\t\t\t\tvaud28-supply = <0x8a>;",
    "\t\t\t\t};",
    "",
]
lines[adc_open:adc_open] = codec

# --- 2. afe node inside the audsys clock-controller@11220000 ---
start = next(i for i, l in enumerate(lines) if "clock-controller@11220000 {" in l)
depth = 0
end = None
for i in range(start, len(lines)):
    depth += lines[i].count("{") - lines[i].count("}")
    if i > start and depth == 0:
        end = i
        break
assert end is not None, "audsys block end not found"
print("audsys block", start + 1, "..", end + 1)

afe = [
    "\t\t\tafe: audio-controller {",
    '\t\t\t\tcompatible = "mediatek,mt6765-afe-pcm";',
    "\t\t\t\tinterrupts = <0x00 0x99 0x04>;",
    "\t\t\t\t#sound-dai-cells = <0x00>;",
    "\t\t\t\tclocks = <0x0e 0x11 0x6f 0xac 0x07 0xac 0x08 0xac 0x09 0xac 0x0a"
    " 0x11 0x40 0x11 0x40 0x11 0x3f 0x11 0x3f 0x11 0x4e 0x11 0x4f 0x11 0x50 0x11 0x51>;",
    '\t\t\t\tclock-names = "top_clk26m_clk", "top_audio_sel", "audio_i2s0_m",'
    ' "audio_i2s1_m", "audio_i2s2_m", "audio_i2s3_m", "engen1", "engen2",'
    ' "aud1", "aud2", "i2s0_m_sel", "i2s1_m_sel", "i2s2_m_sel", "i2s3_m_sel";',
    f"\t\t\t\tphandle = <0x{afe_ph:x}>;",
    '\t\t\t\tstatus = "okay";',
    "\t\t\t};",
    "",
]
lines[end:end] = afe

# --- 3. machine node at root ---
text = "\n".join(lines)
machine = f"""
\tsound {{
\t\tcompatible = "mediatek,mt6765-mt6357";
\t\tmediatek,platform = <0x{afe_ph:x}>;
\t}};
"""
ridx = text.rstrip().rfind("};")
text = text[:ridx] + machine + text[ridx:]
open(f"{WORK}/new.dts", "w").write(text + "\n")

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
