p = "/home/a12bbb/r96-gpu.dts"
s = open(p).read()
old = """					pinmux = <0x1501 0x1601 0x1701 0x1801>;
					drive-strength = <0x08>;"""
new = """					pinmux = <0x1501 0x1601 0x1701 0x1801>;"""
if old in s:
    s = s.replace(old, new, 1)
    open(p, "w").write(s)
    print("drive-strength removed")
else:
    print("pattern not found")
