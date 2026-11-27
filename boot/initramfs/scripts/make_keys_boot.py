import struct, subprocess, sys, re, os

BOOT = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-console2.img"
OUT = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/rootfs/ubuntu/boot/boot-keys.img"
WORK = "/tmp/dtwork"

os.makedirs(WORK, exist_ok=True)
d = bytearray(open(BOOT, "rb").read())
page = struct.unpack_from("<I", d, 36)[0]
hv = struct.unpack_from("<I", d, 40)[0]
ks = struct.unpack_from("<I", d, 8)[0]
rs = struct.unpack_from("<I", d, 16)[0]
ds = struct.unpack_from("<I", d, 1648)[0]
au = lambda x, p: ((x + p - 1) // p) * p
k_off = page
rd_off = k_off + au(ks, page)
dt_off = rd_off + au(rs, page)
kernel = bytes(d[k_off:k_off+ks])
ramdisk = bytes(d[rd_off:rd_off+rs])
dtb = bytes(d[dt_off:dt_off+ds])

open(f"{WORK}/base.dtb", "wb").write(dtb)
subprocess.run(["dtc", "-I", "dtb", "-O", "dts", f"{WORK}/base.dtb", "-o", f"{WORK}/base.dts"], check=True, stderr=subprocess.DEVNULL)
lines = open(f"{WORK}/base.dts").read().splitlines()

# --- patch keypad node ---
out = []
i = 0
inserted = False
while i < len(lines):
    line = lines[i]
    out.append(line)
    if 'keyboard@10010000 {' in line and not inserted:
        # copy until clock-names, then insert props
        while i + 1 < len(lines):
            i += 1
            l = lines[i]
            if 'status = "disabled";' in l:
                out.append('\t\t\tstatus = "okay";')
                continue
            out.append(l)
            if 'clock-names = "kpd";' in l:
                out.append('\t\t\tkeypad,num-rows = <0x09>;')
                out.append('\t\t\tkeypad,num-columns = <0x08>;')
                out.append('\t\t\tdebounce-delay-ms = <0x0f>;')
                out.append('\t\t\tlinux,keymap = <0x00000073 0x00010072>;')
                inserted = True
                break
    i += 1

# --- remove gpio-keys node (top-level, one tab indentation) ---
text = "\n".join(out)
text = re.sub(r"\n\tgpio-keys \{.*?\n\t\};\n", "\n", text, flags=re.S)
text = re.sub(r'(keyboard@10010000 \{.*?)status = "disabled";', r'\1status = "okay";', text, count=1, flags=re.S)

open(f"{WORK}/new.dts", "w").write(text + "\n")
print("inserted props:", inserted, "gpio-keys still present:", "gpio-keys {" in text)

subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", f"{WORK}/new.dtb", f"{WORK}/new.dts"], check=True, stderr=subprocess.DEVNULL)
newdtb = open(f"{WORK}/new.dtb", "rb").read()
print("new dtb size:", len(newdtb), "old:", len(dtb))

hdr = bytearray(d[:page])
struct.pack_into("<I", hdr, 8, len(kernel))
struct.pack_into("<I", hdr, 16, len(ramdisk))
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
