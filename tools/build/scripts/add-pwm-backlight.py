import os, re, subprocess

home = os.path.expanduser("~")
src = os.path.join(home, "r96-alli2c.dts")
out_dts = os.path.join(home, "r96-pwmbl.dts")
out_dtb = os.path.join(home, "r96-pwmbl.dtb")

lines = open(src).read().split("\n")

# 1. disp-pwm: add label, mt8183 fallback, enable
pw = None
for i, ln in enumerate(lines):
    if re.match(r'^\s*pwm@1100e000\s*\{', ln):
        pw = i
        break
if pw is None:
    raise SystemExit("disp-pwm node not found")

ind = re.match(r'^(\s*)', lines[pw]).group(1)
lines[pw] = ind + "disp_pwm: pwm@1100e000 {"

j = pw + 1
while j < len(lines) and not (lines[j].strip() == "};" and re.match(r'^(\s*)', lines[j]).group(1) == ind):
    if '"mediatek,mt6765-disp-pwm"' in lines[j]:
        lines[j] = lines[j].replace('"mediatek,mt6765-disp-pwm";',
                                    '"mediatek,mt6765-disp-pwm", "mediatek,mt8183-disp-pwm";')
    if 'status = "disabled";' in lines[j]:
        lines[j] = lines[j].replace('"disabled"', '"okay"')
    j += 1

# 2. add backlight node inside the root node (before the pin controller or at the end of /)
blk = [
    "",
    "\tbacklight {",
    '\t\tcompatible = "pwm-backlight";',
    "\t\tpwms = <&disp_pwm 0x00 0xf4240>;",
    "\t\tbrightness-levels = <0x00 0x04 0x08 0x10 0x20 0x40 0x60 0x80 0xa0 0xc0 0xe0 0xff>;",
    "\t\tdefault-brightness-level = <0x0a>;",
    "\t\tenable-gpios = <0x10 0x9a 0x00>;",
    "\t};",
]

# insert right before the pin-controller node (inside /soc? no, it's under /soc)
# put it at the very end of the file before the final "};"
idx = len(lines) - 1
while idx > 0 and lines[idx].strip() != "};":
    idx -= 1
lines = lines[:idx] + blk + lines[idx:]

open(out_dts, "w").write("\n".join(lines))
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", out_dtb, out_dts], check=True)
print("dtb:", out_dtb, os.path.getsize(out_dtb))

dts = subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", "/tmp/pwmchk.dts", out_dtb],
                     capture_output=True)
print(subprocess.run(["grep", "-n", "-A6", "backlight {", "/tmp/pwmchk.dts"],
                     capture_output=True, text=True).stdout)
print(subprocess.run(["grep", "-n", "disp-pwm", "/tmp/pwmchk.dts"],
                     capture_output=True, text=True).stdout)
