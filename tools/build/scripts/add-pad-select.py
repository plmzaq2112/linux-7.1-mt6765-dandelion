p = "/home/a12bbb/r96-gpu.dts"
s = open(p).read()

old = """			status = "okay";
			pinctrl-0 = <0xc1>;
			pinctrl-names = "default";
			phandle = <0x9f>;"""
new = """			status = "okay";
			mediatek,pad-select = <0x00>;
			pinctrl-0 = <0xc1>;
			pinctrl-names = "default";
			phandle = <0x9f>;"""
if "mediatek,pad-select" in s:
    print("already present")
else:
    assert old in s
    s = s.replace(old, new, 1)
    open(p, "w").write(s)
    print("pad-select added")
