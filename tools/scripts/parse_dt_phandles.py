import re, sys

path = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/data/dts/dandelion-live.dts"
lines = open(path, encoding="utf-8", errors="replace").read().split("\n")

# build node stack by indentation
node_re = re.compile(r'^(\s*)([A-Za-z0-9_@,.\-]+|\/)\s*\{')
ph = {}
count = 0
for i, ln in enumerate(lines):
    if "phandle = <0x" in ln:
        m = re.search(r'phandle = <(0x[0-9a-f]+)>', ln)
        if not m:
            continue
        count += 1
        target = m.group(1)
        # walk backwards to find the opening brace line of this node
        if "{" in ln:
            # phandle on same line as brace (unlikely)
            node_found = ln
        else:
            node_found = None
            for j in range(i - 1, -1, -1):
                mm = node_re.match(lines[j])
                if mm:
                    node_found = lines[j].strip()
                    break
        ph[target] = node_found

print("phandle count:", count)
for k in ["0x11", "0x28", "0x1d", "0xc0", "0x12", "0x13"]:
    print(k, "->", ph.get(k))

# print the spm node block header + a few power domain children
for i, ln in enumerate(lines):
    if "mediatek,mt6765-scpsys" in ln or "power-controller@10006000" in ln:
        print("\n".join(lines[max(0, i - 3):i + 6]))
        break
