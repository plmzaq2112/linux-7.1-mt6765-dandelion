import os

M = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline")

kconf = os.path.join(M, "sound/soc/mediatek/Kconfig")
s = open(kconf).read()
if "SND_SOC_MT6765" not in s:
    block = """config SND_SOC_MT6765
	tristate "ASoC support for MediaTek MT6765 chip"
	depends on ARCH_MEDIATEK || COMPILE_TEST
	select SND_SOC_MEDIATEK
	help
	  This adds ASoC platform driver support for MediaTek MT6765 chip
	  that can be used with other codecs.
	  Select Y if you have such device.
	  If unsure select "N".

config SND_SOC_MT6765_MT6357
	tristate "ASoC Audio driver for MT6765 with MT6357 codec"
	depends on SND_SOC_MT6765 && MTK_PMIC_WRAP
	select SND_SOC_MT6357
	help
	  This adds support for ASoC machine driver for MediaTek MT6765
	  boards with the MT6357 PMIC codec.
	  Select Y if you have such device.
	  If unsure select "N".

"""
    s = s.replace("\nendmenu", "\n" + block + "endmenu", 1)
    open(kconf, "w").write(s)
    print("Kconfig updated")
else:
    print("Kconfig already has MT6765")

mk = os.path.join(M, "sound/soc/mediatek/Makefile")
s = open(mk).read()
if "mt6765/" not in s:
    s = s.replace("obj-$(CONFIG_SND_SOC_MT8365) += mt8365/",
                  "obj-$(CONFIG_SND_SOC_MT8365) += mt8365/\nobj-$(CONFIG_SND_SOC_MT6765) += mt6765/", 1)
    open(mk, "w").write(s)
    print("Makefile updated")
else:
    print("Makefile already has mt6765")
