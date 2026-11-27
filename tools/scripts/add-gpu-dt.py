import os, re, subprocess

home = os.path.expanduser("~")
src = os.path.join(home, "r96-pwmbl2.dts")
out_dts = os.path.join(home, "r96-gpu.dts")
out_dtb = os.path.join(home, "r96-gpu.dtb")

lines = open(src).read().split("\n")

# insert after the dsi node's closing "};" inside /soc -> find the dsi@14014000 block end
soc_start = None
for i, ln in enumerate(lines):
    if re.match(r'^\s*soc\s*\{', ln):
        soc_start = i
        break
if soc_start is None:
    raise SystemExit("soc node not found")

# find "dsi@14014000 {" then its matching close
dsi = None
for i in range(soc_start, len(lines)):
    if re.match(r'^\s*dsi@14014000\s*\{', lines[i]):
        dsi = i
        break
if dsi is None:
    raise SystemExit("dsi node not found")
ind = re.match(r'^(\s*)', lines[dsi]).group(1)
j = dsi + 1
while j < len(lines):
    if lines[j].strip() == "};" and re.match(r'^(\s*)', lines[j]).group(1) == ind:
        break
    j += 1

ins = [
    "",
    ind + "mfg_cfg@13ffe000 {",
    ind + '\tcompatible = "mediatek,mfgcfg", "syscon";',
    ind + "\treg = <0x00 0x13ffe000 0x00 0x1000>;",
    ind + "\t#clock-cells = <0x01>;",
    ind + "\tphandle = <0xc0>;",
    ind + "};",
    "",
    ind + "mfg_doma@13000000 {",
    ind + '\tcompatible = "mediatek,doma";',
    ind + "\treg = <0x00 0x13000000 0x00 0x80000>;",
    ind + "\tinterrupts = <0x00 0x103 0x08>;",
    ind + '\tinterrupt-names = "RGX";',
    ind + "\tclock-frequency = <0x21f98280>;",
    ind + "\tclocks = <0x11 0x64 0x28 0x04>;",
    ind + '\tclock-names = "mfg", "mfgpll";',
    ind + "\tpower-domains = <0x1d 0x08 0x1d 0x04 0x1d 0x07>;",
    ind + '\tpower-domain-names = "async", "mfg", "core0";',
    ind + "\tmediatek,mfgcfg = <0xc0>;",
    ind + '\tstatus = "okay";',
    ind + "};",
]
lines = lines[:j + 1] + ins + lines[j + 1:]

open(out_dts, "w").write("\n".join(lines))
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", out_dtb, out_dts], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("dtb:", out_dtb, os.path.getsize(out_dtb))

chk = subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", "/tmp/gpuchk.dts", out_dtb],
                     capture_output=True)
print(subprocess.run(["grep", "-A14", "mfg_doma@13000000", "/tmp/gpuchk.dts"],
                     capture_output=True, text=True).stdout)
