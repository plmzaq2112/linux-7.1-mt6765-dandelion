import os, re, subprocess

home = os.path.expanduser("~")
src_dtb = os.path.join(home, "r96-noconsole.dtb")
src_dts = os.path.join(home, "r96-noconsole.dts")
out_dts = os.path.join(home, "r96-bl.dts")
out_dtb = os.path.join(home, "r96-bl.dtb")

subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", src_dts, src_dtb], check=True)
lines = open(src_dts).read().split("\n")

pm = None
for i, ln in enumerate(lines):
    if re.match(r'^\s*pmic@34\s*\{', ln):
        pm = i
        break
if pm is None:
    raise SystemExit("pmic@34 not found")

indent = re.match(r'^(\s*)', lines[pm]).group(1)
child_indent = indent + "\t"

# find first child node (line with deeper indent, ends with '{', no '=')
ins = None
for j in range(pm + 1, len(lines)):
    ln = lines[j]
    if re.match(r'^\s*\}\s*;', ln):
        break
    if ln.startswith(child_indent) and ln.rstrip().endswith("{") and "=" not in ln:
        ins = j
        break
if ins is None:
    raise SystemExit("no child node found in pmic@34")

block = [
    child_indent + "backlight {",
    child_indent + "\tcompatible = \"mediatek,mt6370-backlight\";",
    child_indent + "\tmax-brightness = <0x7ff>;",
    child_indent + "\tdefault-brightness = <0x400>;",
    child_indent + "};",
    "",
]
out = lines[:ins] + block + lines[ins:]
open(out_dts, "w").write("\n".join(out))
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", out_dtb, out_dts], check=True)
print("dtb written:", out_dtb, os.path.getsize(out_dtb), "bytes")

r = subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-", out_dtb], capture_output=True, text=True)
for ln in r.stdout.split("\n"):
    if "mt6370-backlight" in ln or "max-brightness" in ln:
        print("check:", ln.strip())
