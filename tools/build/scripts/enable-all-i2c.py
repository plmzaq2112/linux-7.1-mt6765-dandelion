import os, re, subprocess

home = os.path.expanduser("~")
src = os.path.join(home, "r96-bl2.dts")
out_dts = os.path.join(home, "r96-alli2c.dts")
out_dtb = os.path.join(home, "r96-alli2c.dtb")

# bus -> (controller addr, scl pin, sda pin)
buses = {
    0: ("11007000", 83, 82),
    1: ("11008000", 84, 81),
    2: ("11009000", 103, 104),
    3: ("1100f000", 50, 51),
    4: ("11011000", 105, 106),
    6: ("1100d000", 161, 162),
}

lines = open(src).read().split("\n")

# 1. locate the pin controller node and insert pin groups after the i2c5-pins node
pc = None
for i, ln in enumerate(lines):
    if re.match(r'^\s*pin-controller@10005000\s*\{', ln):
        pc = i
        break
if pc is None:
    raise SystemExit("pin controller not found")

# find end of i2c5-pins block
i5 = None
for i in range(pc, len(lines)):
    if re.match(r'^\s*i2c5-pins\s*\{', lines[i]):
        i5 = i
        break
if i5 is None:
    raise SystemExit("i2c5-pins not found")
base_ind = re.match(r'^(\s*)', lines[i5]).group(1)
j = i5 + 1
while j < len(lines) and not (lines[j].strip() == "};" and len(re.match(r'^(\s*)', lines[j]).group(1)) == len(base_ind)):
    j += 1
ins_at = j + 1

block = []
for b, (addr, scl, sda) in buses.items():
    block += [
        "",
        f"{base_ind}i2c{b}_pins: i2c{b}-pins {{",
        f"{base_ind}\tpins-bus {{",
        f"{base_ind}\t\tpinmux = <0x{scl:02x}01 0x{sda:02x}01>;",
        f"{base_ind}\t\tbias-pull-up;",
        f"{base_ind}\t}};",
        f"{base_ind}}};",
    ]
lines = lines[:ins_at] + block + lines[ins_at:]

# 2. enable controllers, add pinctrl
for b, (addr, scl, sda) in buses.items():
    start = None
    for i, ln in enumerate(lines):
        if re.match(r'^\s*i2c@' + addr + r'\s*\{', ln):
            start = i
            break
    if start is None:
        print("missing i2c@" + addr)
        continue
    ind = re.match(r'^(\s*)', lines[start]).group(1)
    j = start + 1
    has_pinctrl = False
    while j < len(lines):
        if lines[j].strip() == "};" and re.match(r'^(\s*)', lines[j]).group(1) == ind:
            break
        if "status = \"disabled\";" in lines[j]:
            lines[j] = lines[j].replace("disabled", "okay")
        if "pinctrl-0" in lines[j]:
            has_pinctrl = True
        j += 1
    if not has_pinctrl:
        # insert after compatible line
        for k in range(start + 1, j):
            if "compatible" in lines[k]:
                lines.insert(k + 1, f'{ind}\tpinctrl-0 = <&i2c{b}_pins>;')
                lines.insert(k + 2, f'{ind}\tpinctrl-names = "default";')
                j += 2
                break

open(out_dts, "w").write("\n".join(lines))
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", out_dtb, out_dts], check=True)
print("dtb:", out_dtb, os.path.getsize(out_dtb))
