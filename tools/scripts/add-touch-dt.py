import re

p = "/home/a12bbb/r96-gpu.dts"
s = open(p).read()

if "focaltech,fts" in s:
    print("touch node already present, skipping")
    raise SystemExit(0)

# 1) add spi3 pins inside pin-controller (before gpio-keys-pins)
pins = """
			spi3-pins {
				phandle = <0xc1>;

				pins {
					pinmux = <0x1501 0x1601 0x1701 0x1801>;
					drive-strength = <0x08>;
				};
			};
"""
anchor = "\t\t\tgpio-keys-pins {"
assert anchor in s
s = s.replace(anchor, pins + anchor, 1)

# 2) enable spi3 and add touch child
old = """		spi@11013000 {
			compatible = "mediatek,mt6765-spi";
			reg = <0x00 0x11013000 0x00 0x1000>;
			interrupts = <0x00 0x81 0x08>;
			clocks = <0x11 0x0b 0x11 0x6b 0x16 0x28>;
			clock-names = "parent-clk", "sel-clk", "spi-clk";
			#address-cells = <0x01>;
			#size-cells = <0x00>;
			status = "disabled";
			phandle = <0x9f>;
		};"""
new = """		spi@11013000 {
			compatible = "mediatek,mt6765-spi";
			reg = <0x00 0x11013000 0x00 0x1000>;
			interrupts = <0x00 0x81 0x08>;
			clocks = <0x11 0x0b 0x11 0x6b 0x16 0x28>;
			clock-names = "parent-clk", "sel-clk", "spi-clk";
			#address-cells = <0x01>;
			#size-cells = <0x00>;
			status = "okay";
			pinctrl-0 = <0xc1>;
			pinctrl-names = "default";
			phandle = <0x9f>;

			touch@0 {
				compatible = "focaltech,fts";
				reg = <0x00>;
				spi-max-frequency = <0x7a1200>;
				interrupt-parent = <0x10>;
				interrupts = <0x00 0x02>;
				focaltech,reset-gpios = <0x10 0xae 0x00>;
				focaltech,irq-gpios = <0x10 0x00 0x00>;
			};
		};"""
assert old in s, "spi3 node not matched"
s = s.replace(old, new, 1)

open(p, "w").write(s)
print("spi3 + touch node added")
