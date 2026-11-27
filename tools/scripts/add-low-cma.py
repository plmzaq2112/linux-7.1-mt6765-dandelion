import os, re, subprocess, shutil

home = os.path.expanduser("~")
src = os.path.join(home, "r96-gpu.dts")
bak = src + ".bak-cma"
if not os.path.exists(src):
    raise SystemExit("missing " + src)
if not os.path.exists(bak):
    shutil.copy2(src, bak)
    print("backup:", bak)

s = open(src).read()

if "linux,cma" in s:
    print("linux,cma already present, skipping")
else:
    # reserved-memory is empty:
    #   reserved-memory {
    #       #address-cells = <0x02>;
    #       #size-cells = <0x02>;
    #       ranges;
    #   };
    pat = re.compile(r'(\treserved-memory \{\n(?:.*?\n)*?\t\t#address-cells = <0x02>;\n(?:.*?\n)*?\t\tranges;\n)(\t\};)')
    m = pat.search(s)
    if not m:
        raise SystemExit("reserved-memory block not matched")
    body = m.group(1)
    end = m.group(2)
    node = (
        "\n"
        "\t\tlinux,cma {\n"
        "\t\t\tcompatible = \"shared-dma-pool\";\n"
        "\t\t\treusable;\n"
        "\t\t\tlinux,cma-default;\n"
        "\t\t\tsize = <0x02000000>;\n"
        "\t\t\talloc-ranges = <0x00 0x40000000 0x00 0x40000000>;\n"
        "\t\t};\n"
    )
    s = s[:m.start()] + body + node + end + s[m.end():]
    open(src, "w").write(s)
    print("linux,cma node inserted")

out_dtb = os.path.join(home, "r96-gpu.dtb")
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-o", out_dtb, src], check=True)
print("dtb written:", out_dtb, os.path.getsize(out_dtb))

chk = subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-o", "/tmp/cmachk.dts", out_dtb],
                     capture_output=True, text=True)
print(subprocess.run(["grep", "-A10", "linux,cma", "/tmp/cmachk.dts"],
                     capture_output=True, text=True).stdout)
