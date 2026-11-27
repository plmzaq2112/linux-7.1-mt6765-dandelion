import os, re, subprocess

home = os.path.expanduser("~")
src = os.path.join(home, "r96-bl.dts")
out = os.path.join(home, "r96-bl2.dtb")

if not os.path.exists(src):
    raise SystemExit("missing " + src)

lines = open(src).read().split("\n")
in_i2c5 = False
changed = 0
depth = 0
for i, ln in enumerate(lines):
    if re.match(r'^\s*i2c5-pins\s*\{', ln):
        in_i2c5 = True
        depth = len(ln) - len(ln.lstrip('\t'))
        continue
    if in_i2c5:
        ind = len(ln) - len(ln.lstrip('\t'))
        if ln.strip() == "};" and ind <= depth:
            in_i2c5 = False
            continue
        if "bias-disable" in ln:
            lines[i] = ln.replace("bias-disable", "bias-pull-up")
            changed += 1

if changed == 0:
    raise SystemExit("no bias-disable found in i2c5-pins")

tmp = os.path.join(home, "r96-bl2.dts")
open(tmp, "w").write("\n".join(lines))
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", out, tmp], check=True)
print("changed", changed, "->", out, os.path.getsize(out))

r = subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", os.path.join(home, "bl2chk.dts"), out], check=True)
print(subprocess.run(["grep", "-A5", "i2c5-pins", os.path.join(home, "bl2chk.dts")],
                     capture_output=True, text=True).stdout)
